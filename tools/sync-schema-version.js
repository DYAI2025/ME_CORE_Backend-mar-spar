#!/usr/bin/env node
/**
 * Schema Version Synchronization Tool
 * Ensures consistent schema versions across backend, frontend, and Spark
 */

const fs = require('fs').promises;
const path = require('path');
const crypto = require('crypto');

const SCHEMA_LOCATIONS = {
  backend: {
    path: '../backend/schemata',
    pattern: /^v\d+\.\d+\.json$/
  },
  frontend: {
    path: '../frontend/src/shared/schemas',
    pattern: /\.ts$/
  },
  spark: {
    path: '../spark-nlp/src/schemas',
    pattern: /\.py$/
  }
};

class SchemaSync {
  constructor() {
    this.schemas = new Map();
    this.currentVersion = null;
  }

  async run() {
    console.log('🔄 Starting Schema Version Synchronization...\n');
    
    try {
      // Step 1: Scan all schema locations
      await this.scanSchemas();
      
      // Step 2: Determine current version
      this.determineCurrentVersion();
      
      // Step 3: Generate TypeScript interfaces
      await this.generateTypeScriptInterfaces();
      
      // Step 4: Generate Python models
      await this.generatePythonModels();
      
      // Step 5: Update version manifest
      await this.updateVersionManifest();
      
      // Step 6: Validate consistency
      await this.validateConsistency();
      
      console.log('\n✅ Schema synchronization completed successfully!');
      
    } catch (error) {
      console.error('\n❌ Schema synchronization failed:', error.message);
      process.exit(1);
    }
  }

  async scanSchemas() {
    console.log('📂 Scanning schema files...');
    
    const backendPath = path.join(__dirname, SCHEMA_LOCATIONS.backend.path);
    const files = await fs.readdir(backendPath);
    
    for (const file of files) {
      if (SCHEMA_LOCATIONS.backend.pattern.test(file)) {
        const filePath = path.join(backendPath, file);
        const content = await fs.readFile(filePath, 'utf8');
        const schema = JSON.parse(content);
        
        const version = file.replace('.json', '');
        this.schemas.set(version, {
          file,
          path: filePath,
          content: schema,
          hash: this.calculateHash(content)
        });
        
        console.log(`  ✓ Found schema: ${version}`);
      }
    }
    
    console.log(`\n📊 Total schemas found: ${this.schemas.size}`);
  }

  determineCurrentVersion() {
    // Get the latest version based on semantic versioning
    const versions = Array.from(this.schemas.keys()).sort((a, b) => {
      const [aMajor, aMinor] = a.substring(1).split('.').map(Number);
      const [bMajor, bMinor] = b.substring(1).split('.').map(Number);
      
      if (aMajor !== bMajor) return bMajor - aMajor;
      return bMinor - aMinor;
    });
    
    this.currentVersion = versions[0];
    console.log(`\n🏷️  Current schema version: ${this.currentVersion}`);
  }

  async generateTypeScriptInterfaces() {
    console.log('\n📝 Generating TypeScript interfaces...');
    
    const schema = this.schemas.get(this.currentVersion);
    const outputPath = path.join(
      __dirname,
      '../frontend/src/shared/types/schema.ts'
    );
    
    const tsContent = this.schemaToTypeScript(schema.content);
    
    // Ensure directory exists
    await fs.mkdir(path.dirname(outputPath), { recursive: true });
    await fs.writeFile(outputPath, tsContent);
    
    console.log(`  ✓ Generated: ${outputPath}`);
  }

  async generatePythonModels() {
    console.log('\n🐍 Generating Python models...');
    
    const schema = this.schemas.get(this.currentVersion);
    const outputPath = path.join(
      __dirname,
      '../spark-nlp/src/models/schema.py'
    );
    
    const pyContent = this.schemaToPython(schema.content);
    
    // Ensure directory exists
    await fs.mkdir(path.dirname(outputPath), { recursive: true });
    await fs.writeFile(outputPath, pyContent);
    
    console.log(`  ✓ Generated: ${outputPath}`);
  }

  schemaToTypeScript(schema) {
    let ts = `/**
 * Auto-generated TypeScript interfaces from JSON Schema
 * Version: ${this.currentVersion}
 * Generated: ${new Date().toISOString()}
 * DO NOT EDIT MANUALLY
 */

`;

    // Generate Marker interface
    ts += `export interface Marker {
  _id: string;
  frame: MarkerFrame;
  examples?: string[];
  pattern?: string;
  composed_of?: string[];
  detect_class?: string;
  activation?: ActivationRule;
  metadata?: MarkerMetadata;
}

export interface MarkerFrame {
  signal: string;
  concept: string;
  pragmatics: string;
  narrative: string;
}

export interface ActivationRule {
  type: 'ALL' | 'ANY' | 'ANY_N' | 'TEMPORAL' | 'SENTIMENT' | 'PROXIMITY' | 'NEGATION' | 'PATTERN' | 'COMPOSITE';
  components?: string[];
  n?: number;
  window?: number;
  strict_order?: boolean;
  sentiment_alignment?: 'positive' | 'negative' | 'neutral';
  max_distance?: number;
  allows_negation?: boolean;
  pattern?: string;
  rules?: ActivationRule[];
}

export interface MarkerMetadata {
  category?: string;
  confidence?: number;
  version?: string;
  tags?: string[];
}

export interface AnalysisResult {
  request_id: string;
  status: 'success' | 'error';
  text: string;
  markers: DetectedMarker[];
  marker_count: number;
  nlp_enriched: boolean;
  metadata: AnalysisMetadata;
}

export interface DetectedMarker {
  marker_id: string;
  confidence: number;
  detection_phase: 'initial' | 'contextual';
  position?: MarkerPosition;
  components?: string[];
}

export interface MarkerPosition {
  start: number;
  end: number;
  sentence_index?: number;
}

export interface AnalysisMetadata {
  session_id?: string;
  schema_id?: string;
  phases: PhaseMetadata;
  nlp_service: string;
}

export interface PhaseMetadata {
  phase1: { markers_found: number; error?: string };
  phase2: { enrichment: any; error?: string };
  phase3: { markers_added: number; error?: string };
}

export const SCHEMA_VERSION = '${this.currentVersion}';
`;

    return ts;
  }

  schemaToPython(schema) {
    let py = `"""
Auto-generated Python models from JSON Schema
Version: ${this.currentVersion}
Generated: ${new Date().toISOString()}
DO NOT EDIT MANUALLY
"""
from typing import List, Dict, Any, Optional, Union, Literal
from pydantic import BaseModel, Field
from datetime import datetime


class MarkerFrame(BaseModel):
    """Marker frame containing semantic information"""
    signal: str
    concept: str
    pragmatics: str
    narrative: str


class ActivationRule(BaseModel):
    """Activation rule for complex markers"""
    type: Literal[
        'ALL', 'ANY', 'ANY_N', 'TEMPORAL', 'SENTIMENT',
        'PROXIMITY', 'NEGATION', 'PATTERN', 'COMPOSITE'
    ]
    components: Optional[List[str]] = None
    n: Optional[int] = None
    window: Optional[int] = None
    strict_order: Optional[bool] = False
    sentiment_alignment: Optional[Literal['positive', 'negative', 'neutral']] = None
    max_distance: Optional[int] = None
    allows_negation: Optional[bool] = True
    pattern: Optional[str] = None
    rules: Optional[List['ActivationRule']] = None


class MarkerMetadata(BaseModel):
    """Additional marker metadata"""
    category: Optional[str] = None
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    version: Optional[str] = None
    tags: Optional[List[str]] = None


class Marker(BaseModel):
    """Complete marker definition"""
    id: str = Field(..., alias='_id')
    frame: MarkerFrame
    examples: Optional[List[str]] = None
    pattern: Optional[str] = None
    composed_of: Optional[List[str]] = None
    detect_class: Optional[str] = None
    activation: Optional[ActivationRule] = None
    metadata: Optional[MarkerMetadata] = None
    
    class Config:
        populate_by_name = True


class MarkerPosition(BaseModel):
    """Position of detected marker in text"""
    start: int
    end: int
    sentence_index: Optional[int] = None


class DetectedMarker(BaseModel):
    """Detected marker with metadata"""
    marker_id: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    detection_phase: Literal['initial', 'contextual']
    position: Optional[MarkerPosition] = None
    components: Optional[List[str]] = None


class PhaseMetadata(BaseModel):
    """Metadata for analysis phases"""
    phase1: Dict[str, Any]
    phase2: Dict[str, Any]
    phase3: Dict[str, Any]


class AnalysisMetadata(BaseModel):
    """Analysis metadata"""
    session_id: Optional[str] = None
    schema_id: Optional[str] = None
    phases: PhaseMetadata
    nlp_service: str


class AnalysisResult(BaseModel):
    """Complete analysis result"""
    request_id: str
    status: Literal['success', 'error']
    text: str
    markers: List[DetectedMarker]
    marker_count: int
    nlp_enriched: bool
    metadata: AnalysisMetadata
    error: Optional[str] = None


# Schema version constant
SCHEMA_VERSION = '${this.currentVersion}'


# Update forward references
ActivationRule.model_rebuild()
`;

    return py;
  }

  async updateVersionManifest() {
    console.log('\n📋 Updating version manifest...');
    
    const manifest = {
      current_version: this.currentVersion,
      updated_at: new Date().toISOString(),
      schemas: {}
    };
    
    for (const [version, data] of this.schemas.entries()) {
      manifest.schemas[version] = {
        file: data.file,
        hash: data.hash,
        markers_count: Object.keys(data.content.markers || {}).length
      };
    }
    
    const manifestPath = path.join(__dirname, '../version-manifest.json');
    await fs.writeFile(
      manifestPath,
      JSON.stringify(manifest, null, 2)
    );
    
    console.log(`  ✓ Updated: ${manifestPath}`);
  }

  async validateConsistency() {
    console.log('\n🔍 Validating consistency...');
    
    // Check if generated files exist
    const checks = [
      {
        name: 'TypeScript interfaces',
        path: '../frontend/src/shared/types/schema.ts'
      },
      {
        name: 'Python models',
        path: '../spark-nlp/src/models/schema.py'
      },
      {
        name: 'Version manifest',
        path: '../version-manifest.json'
      }
    ];
    
    let allValid = true;
    
    for (const check of checks) {
      const fullPath = path.join(__dirname, check.path);
      try {
        await fs.access(fullPath);
        console.log(`  ✓ ${check.name}: OK`);
      } catch {
        console.log(`  ❌ ${check.name}: MISSING`);
        allValid = false;
      }
    }
    
    if (!allValid) {
      throw new Error('Consistency validation failed');
    }
  }

  calculateHash(content) {
    return crypto
      .createHash('sha256')
      .update(content)
      .digest('hex')
      .substring(0, 8);
  }
}

// Run the tool
if (require.main === module) {
  const sync = new SchemaSync();
  sync.run();
}

module.exports = SchemaSync;