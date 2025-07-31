"""
Complete Spark NLP Service implementation for MarkerEngine.
Provides advanced NLP capabilities with German language support.
"""
import os
import logging
from typing import Optional, List, Dict, Any
from pyspark.sql import SparkSession
from pyspark.ml import Pipeline
import sparknlp
from sparknlp.annotator import (
    DocumentAssembler,
    SentenceDetector,
    Tokenizer,
    WordEmbeddingsModel,
    NerDLModel,
    PerceptronModel,
    DependencyParserModel,
    LemmatizerModel,
    SentimentDetector,
    StopWordsCleaner
)
from sparknlp.base import Finisher
from ..models.analysis_context import AnalysisContext
from ..services.nlp_service import NlpService

logger = logging.getLogger(__name__)


class SparkNlpServiceImpl(NlpService):
    """
    Full Spark NLP implementation with German language support.
    Provides comprehensive NLP annotations for semantic reasoning.
    """
    
    # Model names for German language
    GERMAN_MODELS = {
        'embeddings': 'glove_840B_300',  # Multilingual embeddings
        'ner': 'ner_ud_gsd_cc_300d',     # German NER model
        'pos': 'pos_ud_gsd',             # German POS tagger
        'dependency': 'dependency_conllu', # German dependency parser
        'lemma': 'lemma',                # German lemmatizer
        'stopwords': 'stopwords_de'      # German stopwords
    }
    
    def __init__(self):
        """Initialize Spark NLP service with German language models."""
        self._available = False
        self._spark = None
        self._pipeline = None
        self._initialized = False
        
        try:
            self._initialize_spark()
            self._available = True
        except Exception as e:
            logger.error(f"Failed to initialize Spark NLP: {e}")
    
    def _initialize_spark(self):
        """Initialize Spark session with optimized settings."""
        logger.info("Initializing Spark session for NLP...")
        
        # Spark configuration for optimal performance
        self._spark = SparkSession.builder \
            .appName("MarkerEngine_NLP") \
            .master("local[*]") \
            .config("spark.driver.memory", "4g") \
            .config("spark.driver.maxResultSize", "2g") \
            .config("spark.serializer", "org.apache.spark.serializer.KryoSerializer") \
            .config("spark.kryoserializer.buffer.max", "2000M") \
            .config("spark.sql.adaptive.enabled", "true") \
            .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
            .getOrCreate()
        
        # Initialize Spark NLP
        sparknlp.start(spark=self._spark)
        logger.info("Spark NLP initialized successfully")
    
    def _build_pipeline(self) -> Pipeline:
        """Build the NLP pipeline with German language models."""
        logger.info("Building German NLP pipeline...")
        
        # Document assembler
        document_assembler = DocumentAssembler() \
            .setInputCol("text") \
            .setOutputCol("document")
        
        # Sentence detection
        sentence_detector = SentenceDetector() \
            .setInputCols(["document"]) \
            .setOutputCol("sentence") \
            .setUseAbbreviations(True) \
            .setCustomBounds([".", "!", "?", "...", "。"])
        
        # Tokenization
        tokenizer = Tokenizer() \
            .setInputCols(["sentence"]) \
            .setOutputCol("token")
        
        # German word embeddings
        try:
            embeddings = WordEmbeddingsModel.pretrained(
                self.GERMAN_MODELS['embeddings'], 'xx'
            ) \
            .setInputCols(["sentence", "token"]) \
            .setOutputCol("embeddings") \
            .setCaseSensitive(False)
        except Exception as e:
            logger.warning(f"Could not load embeddings model: {e}")
            embeddings = None
        
        # German POS tagger
        pos_tagger = PerceptronModel.pretrained(
            self.GERMAN_MODELS['pos'], 'de'
        ) \
        .setInputCols(["sentence", "token"]) \
        .setOutputCol("pos")
        
        # German lemmatizer
        lemmatizer = LemmatizerModel.pretrained(
            self.GERMAN_MODELS['lemma'], 'de'
        ) \
        .setInputCols(["token"]) \
        .setOutputCol("lemma")
        
        # German stopwords cleaner
        stopwords_cleaner = StopWordsCleaner.pretrained(
            self.GERMAN_MODELS['stopwords'], 'de'
        ) \
        .setInputCols(["token"]) \
        .setOutputCol("clean_tokens") \
        .setCaseSensitive(False)
        
        # German NER
        try:
            ner = NerDLModel.pretrained(
                self.GERMAN_MODELS['ner'], 'de'
            ) \
            .setInputCols(["sentence", "token", "embeddings"]) \
            .setOutputCol("ner")
        except Exception as e:
            logger.warning(f"Could not load NER model: {e}")
            ner = None
        
        # German dependency parser
        try:
            dependency_parser = DependencyParserModel.pretrained(
                self.GERMAN_MODELS['dependency'], 'de'
            ) \
            .setInputCols(["sentence", "pos", "token"]) \
            .setOutputCol("dependency")
        except Exception as e:
            logger.warning(f"Could not load dependency parser: {e}")
            dependency_parser = None
        
        # Sentiment detector (using rule-based approach for German)
        # Note: For production, use a German-specific sentiment model
        sentiment_detector = SentimentDetector() \
            .setInputCols(["sentence", "token"]) \
            .setOutputCol("sentiment") \
            .setDictionary("resources/sentiment/german_sentiment_dict.txt", 
                         delimiter=",", readAs="TEXT", options={"format": "text"})
        
        # Finisher to clean up annotations
        finisher = Finisher() \
            .setInputCols(["token", "pos", "lemma", "clean_tokens", "ner", "sentiment"]) \
            .setOutputCols(["token_array", "pos_array", "lemma_array", 
                           "clean_tokens_array", "ner_array", "sentiment_array"]) \
            .setCleanAnnotations(False)
        
        # Build pipeline stages
        stages = [
            document_assembler,
            sentence_detector,
            tokenizer,
            pos_tagger,
            lemmatizer,
            stopwords_cleaner
        ]
        
        # Add optional stages if models loaded successfully
        if embeddings:
            stages.append(embeddings)
        if ner and embeddings:  # NER requires embeddings
            stages.append(ner)
        if dependency_parser:
            stages.append(dependency_parser)
        
        stages.append(finisher)
        
        # Create pipeline
        pipeline = Pipeline(stages=stages)
        logger.info(f"Pipeline built with {len(stages)} stages")
        
        return pipeline
    
    def enrich(self, context: AnalysisContext) -> None:
        """
        Enrich context with comprehensive Spark NLP annotations.
        
        Args:
            context: The AnalysisContext to enrich with NLP data
        """
        if not self._available or not context.text:
            logger.warning("SparkNlpService not available or empty text")
            return
        
        try:
            # Lazy initialization of pipeline
            if not self._initialized:
                self._pipeline = self._build_pipeline()
                self._initialized = True
            
            # Create DataFrame from text
            data = self._spark.createDataFrame([(context.text,)], ["text"])
            
            # Run NLP pipeline
            logger.debug(f"Processing text with {len(context.text)} characters")
            result = self._pipeline.fit(data).transform(data)
            
            # Extract results
            annotations = result.collect()[0]
            
            # Process tokens
            if 'token_array' in annotations:
                context.tokens = annotations['token_array']
                logger.debug(f"Extracted {len(context.tokens)} tokens")
            
            # Process sentences
            if 'sentence' in annotations:
                sentences = annotations['sentence']
                context.sentences = [s.result for s in sentences]
                logger.debug(f"Extracted {len(context.sentences)} sentences")
            
            # Process POS tags
            if 'pos_array' in annotations:
                pos_tags = annotations['pos_array']
                context.pos_tags = [
                    {"token": token, "pos": pos} 
                    for token, pos in zip(context.tokens, pos_tags)
                ]
            
            # Process lemmas
            if 'lemma_array' in annotations:
                lemmas = annotations['lemma_array']
                context.lemmas = [
                    {"token": token, "lemma": lemma}
                    for token, lemma in zip(context.tokens, lemmas)
                ]
            
            # Process clean tokens (without stopwords)
            if 'clean_tokens_array' in annotations:
                context.clean_tokens = annotations['clean_tokens_array']
            
            # Process named entities
            if 'ner_array' in annotations:
                ner_tags = annotations['ner_array']
                # Group consecutive entities
                context.named_entities = self._group_entities(context.tokens, ner_tags)
                logger.debug(f"Extracted {len(context.named_entities)} entities")
            
            # Process dependencies
            if 'dependency' in annotations:
                dependencies = annotations['dependency']
                context.dependency_parse = [
                    {
                        "token": dep.result,
                        "dependency": dep.metadata.get('dep', ''),
                        "head": dep.metadata.get('head', ''),
                        "head_index": dep.metadata.get('head_index', -1)
                    }
                    for dep in dependencies
                ]
            
            # Process sentiment
            if 'sentiment_array' in annotations:
                sentiments = annotations['sentiment_array']
                context.sentiment_scores = self._calculate_sentiment_scores(sentiments)
            
            # Add metadata
            context.metadata.update({
                "nlp_service": "spark_nlp",
                "nlp_version": sparknlp.version(),
                "language": "de",
                "models_used": list(self.GERMAN_MODELS.keys()),
                "token_count": len(context.tokens) if context.tokens else 0,
                "sentence_count": len(context.sentences) if context.sentences else 0
            })
            
            logger.info(f"NLP enrichment complete: {context.metadata['token_count']} tokens, "
                       f"{context.metadata['sentence_count']} sentences")
            
        except Exception as e:
            logger.error(f"Error during NLP enrichment: {e}", exc_info=True)
            # Fallback to basic processing
            self._fallback_processing(context)
    
    def _group_entities(self, tokens: List[str], ner_tags: List[str]) -> List[Dict[str, Any]]:
        """Group consecutive named entity tokens."""
        entities = []
        current_entity = None
        
        for i, (token, tag) in enumerate(zip(tokens, ner_tags)):
            if tag != 'O':  # Not outside an entity
                if tag.startswith('B-'):  # Beginning of entity
                    if current_entity:
                        entities.append(current_entity)
                    current_entity = {
                        'text': token,
                        'entity': tag[2:],  # Remove B- prefix
                        'start': i,
                        'end': i + 1
                    }
                elif tag.startswith('I-') and current_entity:  # Inside entity
                    current_entity['text'] += ' ' + token
                    current_entity['end'] = i + 1
            else:
                if current_entity:
                    entities.append(current_entity)
                    current_entity = None
        
        if current_entity:
            entities.append(current_entity)
        
        return entities
    
    def _calculate_sentiment_scores(self, sentiments: List[str]) -> Dict[str, float]:
        """Calculate overall sentiment scores from token sentiments."""
        sentiment_counts = {'positive': 0, 'negative': 0, 'neutral': 0}
        
        for sentiment in sentiments:
            if sentiment in sentiment_counts:
                sentiment_counts[sentiment] += 1
        
        total = sum(sentiment_counts.values())
        if total == 0:
            return {'positive': 0.0, 'negative': 0.0, 'neutral': 1.0}
        
        return {
            sent: count / total 
            for sent, count in sentiment_counts.items()
        }
    
    def _fallback_processing(self, context: AnalysisContext):
        """Fallback to basic processing if Spark NLP fails."""
        logger.info("Using fallback processing")
        
        # Basic tokenization
        context.tokens = context.text.split()
        context.sentences = [context.text]
        
        # Add metadata
        context.metadata.update({
            "nlp_service": "spark_nlp_fallback",
            "nlp_version": "1.0.0",
            "error": "Spark NLP processing failed, using fallback"
        })
    
    def is_available(self) -> bool:
        """Check if Spark NLP service is available."""
        return self._available and self._spark is not None
    
    def shutdown(self):
        """Shutdown Spark session gracefully."""
        if self._spark:
            logger.info("Shutting down Spark session...")
            self._spark.stop()
            self._spark = None
            self._available = False
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about loaded models."""
        return {
            "available": self._available,
            "initialized": self._initialized,
            "spark_version": self._spark.version if self._spark else None,
            "spark_nlp_version": sparknlp.version() if self._available else None,
            "models": self.GERMAN_MODELS,
            "memory_usage": self._get_memory_usage() if self._spark else None
        }
    
    def _get_memory_usage(self) -> Dict[str, str]:
        """Get current memory usage of Spark."""
        if not self._spark:
            return {}
        
        try:
            status = self._spark.sparkContext.statusTracker()
            return {
                "driver_memory": self._spark.conf.get("spark.driver.memory"),
                "executor_memory": self._spark.conf.get("spark.executor.memory", "default"),
                "active_jobs": len(status.getActiveJobIds()),
                "active_stages": len(status.getActiveStageIds())
            }
        except Exception as e:
            logger.warning(f"Could not get memory usage: {e}")
            return {}