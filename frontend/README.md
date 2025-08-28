# 🎯 Markerengine Frontend

**Beta-GUI Frontend für Markerengine-Architektur**  
Text-Analyse, Demonstrationen, Testing und Content Management

## 📋 Projekt-Übersicht

Dieses Frontend wurde aus dem ursprünglichen [realtime-fraud-detection-with-gnn-on-dgl](https://github.com/DYAI2025/realtime-fraud-detection-with-gnn-on-dgl.git) Repository isoliert und als eigenständiger Service für die Markerengine-Architektur neu entwickelt.

### 🎯 **Kernfunktionen**

#### **Input-Card**
- **Textarea**: Eingabe von bis zu 4.000 Zeichen für Text-Analyse
- **Schema-Auswahl**: Dropdown-Menü für vordefinierte Analyse-Schemata
- **Analyse-Button**: Startet die Marker-Analyse
- **Clear-Button**: Leert das Eingabeformular

#### **Result-Grid**
- **Risk Gauge**: Visuelle Risikoanzeige im Ampel-Stil (grün/gelb/rot)
- **Marker-Chips**: Farbcodierte Chips für erkannte Marker
- **Markdown-Interpretation**: Korrekte Darstellung von Markdown-Text
- **Text-Highlighting**: Farbliche Hervorhebung erkannter Marker im Text

#### **Live-Log Drawer**
- **WebSocket-Verbindung**: Echtzeit-Kommunikation für Live-Updates
- **Log-Anzeige**: Schritt-für-Schritt-Verfolgung der Analyse
- **Ausklappbarer Bereich**: Drawer-Interface für Live-Logs

## 🛠️ **Technologie-Stack**

### **Core Technologies**
- **Next.js 14**: React Framework mit App Router
- **TypeScript**: Typisierte Entwicklung
- **Tailwind CSS**: Utility-First CSS Framework
- **shadcn/ui**: Moderne UI-Komponenten

### **UI & Design**
- **Radix UI Primitives**: Accessible UI Components
- **Lucide React**: Icon-Bibliothek
- **Recharts**: Datenvisualisierung
- **React Markdown**: Markdown-Rendering

### **Real-time Features**
- **WebSockets (WS)**: Live-Log-Streaming
- **Sonner**: Toast-Benachrichtigungen

### **Authentication & Security**
- **JWT-Authentifizierung**: Sichere Benutzeranmeldung
- **Rate-Limit-Anzeige**: Live-Status der API-Limits

## 📁 **Projektstruktur**

```
markerengine-frontend/
├── src/
│   ├── app/                    # Next.js 14 App Router
│   │   ├── globals.css        # Globale Styles + shadcn/ui
│   │   ├── layout.tsx         # Root Layout
│   │   ├── page.tsx           # Hauptseite
│   │   └── api/               # API Routes
│   ├── components/            # React Komponenten
│   │   ├── ui/                # shadcn/ui Basis-Komponenten
│   │   ├── input-card.tsx     # Eingabe-Komponente
│   │   ├── result-grid.tsx    # Ergebnis-Anzeige
│   │   ├── risk-gauge.tsx     # Risiko-Anzeige
│   │   ├── marker-chip.tsx    # Marker-Chips
│   │   ├── live-log-drawer.tsx # Live-Log-Drawer
│   │   └── theme-provider.tsx # Dark-Mode Provider
│   ├── hooks/                 # Custom React Hooks
│   ├── lib/                   # Utility-Funktionen
│   ├── types/                 # TypeScript-Typen
│   └── utils/                 # Helper-Funktionen
├── package.json               # Dependencies
├── tailwind.config.js         # Tailwind-Konfiguration
├── tsconfig.json             # TypeScript-Konfiguration
└── README.md                 # Diese Datei
```

## 🎨 **Design-Features**

### **Responsive Design**
- **Mobile-First**: Optimiert für alle Bildschirmgrößen
- **Adaptive Layout**: Flexibles Grid-System
- **Touch-Friendly**: Mobile-optimierte Interaktionen

### **Dark Mode**
- **System-Preference**: Automatische Erkennung des System-Themes
- **Toggle-Switch**: Manueller Wechsel zwischen hell/dunkel
- **Smooth Transitions**: Animierte Theme-Wechsel

### **Accessibility (a11y)**
- **WCAG 2.1 AA**: Barrierefreiheits-Standards
- **Keyboard Navigation**: Vollständige Tastatur-Bedienung
- **Screen Reader**: Unterstützung für Hilfstechnologien
- **High Contrast**: Kontrastreiche Farbgebung

## 🚀 **Installation & Setup**

### **1. Dependencies installieren**
```bash
npm install
# oder
yarn install
```

### **2. Environment Variables**
```bash
# .env.local erstellen
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
NEXT_PUBLIC_APP_NAME=Markerengine Frontend
```

### **3. Development Server starten**
```bash
npm run dev
# oder
yarn dev
```

### **4. Production Build**
```bash
npm run build
npm start
```

## 🔧 **Konfiguration**

### **Markerengine API Integration**
```typescript
// src/lib/api.ts
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL

export const api = {
  analyze: (request: AnalysisRequest) => 
    fetch(`${API_BASE_URL}/analyze`, { /* ... */ }),
  
  getSchemas: () => 
    fetch(`${API_BASE_URL}/schemas`),
    
  // ... weitere API-Calls
}
```

### **WebSocket Konfiguration**
```typescript
// src/hooks/useWebSocket.ts
const WS_URL = process.env.NEXT_PUBLIC_WS_URL

export const useWebSocket = () => {
  // WebSocket-Logik für Live-Logs
}
```

## 📊 **Komponenten-Details**

### **Input-Card**
```typescript
interface InputCardProps {
  onAnalyze: (request: AnalysisRequest) => void
  schemas: AnalysisSchema[]
  isLoading?: boolean
  maxCharacters?: number
}
```

**Features:**
- Character-Counter mit 4.000-Zeichen-Limit
- Schema-Dropdown mit Suchfunktion
- Validation und Error-Handling
- Loading-States mit Skeleton-UI

### **Risk Gauge**
```typescript
interface RiskGaugeProps {
  score: number // 0.0 - 1.0
  size?: 'sm' | 'md' | 'lg'
  showLabel?: boolean
}
```

**Features:**
- Animierte Circular Progress Bar
- Farb-Coding: Grün (niedrig), Gelb (mittel), Rot (hoch)
- Responsive Größenanpassung
- Accessibility-Labels

### **Marker-Chips**
```typescript
interface MarkerChipProps {
  marker: DetectedMarker
  onClick?: (marker: DetectedMarker) => void
  size?: 'sm' | 'md' | 'lg'
}
```

**Features:**
- Farbcodierung nach Kategorie
- Hover-Effekte und Animationen
- Click-Handler für Interaktivität
- Confidence-Score-Anzeige

### **Live-Log Drawer**
```typescript
interface LiveLogDrawerProps {
  isOpen: boolean
  onClose: () => void
  entries: LiveLogEntry[]
}
```

**Features:**
- Slide-in/out Animationen
- Auto-Scroll zu neuen Einträgen
- Farbcodierung nach Log-Level
- WebSocket-Integration

## 🔐 **Sicherheit & Authentifizierung**

### **JWT-Authentifizierung**
```typescript
// Authentication Hook
export const useAuth = () => {
  const [user, setUser] = useState<AuthUser | null>(null)
  
  const login = async (credentials) => {
    // JWT-Login-Logik
  }
  
  const logout = () => {
    // Logout-Logik
  }
  
  return { user, login, logout }
}
```

### **Rate-Limit-Anzeige**
```typescript
// Rate-Limit-Status
export const RateLimitIndicator = ({ rateLimit }: Props) => {
  const { percentage, level, remaining } = formatRateLimit(
    rateLimit.limit - rateLimit.remaining,
    rateLimit.limit
  )
  
  return (
    <div className={`rate-limit-indicator rate-limit-${level}`}>
      {remaining} / {rateLimit.limit} Requests remaining
    </div>
  )
}
```

## 📱 **Responsive Breakpoints**

```css
/* Tailwind CSS Breakpoints */
sm: 640px   /* Tablets */
md: 768px   /* Small Laptops */
lg: 1024px  /* Laptops */
xl: 1280px  /* Desktops */
2xl: 1536px /* Large Desktops */
```

## 🎯 **Performance-Optimierungen**

### **Code-Splitting**
- **Dynamic Imports**: Lazy-Loading von Komponenten
- **Route-based Splitting**: Automatisches Splitting durch Next.js
- **Component-level Splitting**: Conditional Loading

### **Caching**
- **React Query**: API-Response-Caching
- **Next.js ISR**: Incremental Static Regeneration
- **Browser-Caching**: Service Worker für Offline-Support

### **Bundle-Optimierung**
- **Tree-Shaking**: Automatische Entfernung ungenutzten Codes
- **Minification**: Komprimierung von JS/CSS
- **Image-Optimierung**: Next.js Image-Komponente

## 🧪 **Testing**

### **Test-Setup**
```bash
# Test-Dependencies installieren
npm install --save-dev @testing-library/react @testing-library/jest-dom jest

# Tests ausführen
npm run test
npm run test:watch
npm run test:coverage
```

### **Test-Struktur**
```
src/
├── __tests__/
├── components/
│   └── __tests__/
└── hooks/
    └── __tests__/
```

## 🚀 **Deployment**

### **Render (Empfohlen)**
```bash
# 1. Push zu GitHub
git add .
git commit -m "Add Render deployment config"
git push origin main

# 2. Auf Render.com:
# - Neuen Web Service erstellen
# - GitHub Repository verbinden
# - markerengine_frontend als Root Directory wählen
# - Render erkennt render.yaml automatisch
# - Environment Variables setzen:
#   NEXT_PUBLIC_API_URL=https://your-backend.onrender.com/api
#   NEXT_PUBLIC_WS_URL=wss://your-backend.onrender.com/ws
```

### **Vercel**
```bash
npm install -g vercel
vercel --prod
```

### **Docker**
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "start"]
```

### **Static Export**
```bash
npm run build
npm run export
```

## 📚 **API-Integration**

### **Markerengine Backend Endpoints**
```typescript
// Analyse-Endpunkt
POST /api/analyze
{
  "text": "Text zur Analyse...",
  "schemaId": "schema-uuid",
  "options": {
    "highlightMarkers": true,
    "includeConfidence": true
  }
}

// Schema-Endpunkte
GET /api/schemas          # Alle Schemata
GET /api/schemas/:id      # Einzelnes Schema
POST /api/schemas         # Neues Schema erstellen

// WebSocket-Endpunkt
WS /ws/logs              # Live-Log-Stream
```

## 🎨 **Theming & Customization**

### **CSS Custom Properties**
```css
:root {
  /* Markerengine Brand Colors */
  --marker-primary: #2563eb;
  --marker-secondary: #7c3aed;
  --marker-success: #16a34a;
  --marker-warning: #ea580c;
  --marker-error: #dc2626;
}
```

### **Tailwind Extensions**
```javascript
// tailwind.config.js - Custom Colors
colors: {
  marker: {
    risk: {
      low: 'hsl(120, 70%, 50%)',
      medium: 'hsl(45, 100%, 50%)',
      high: 'hsl(0, 70%, 50%)',
    }
  }
}
```

## 🐛 **Troubleshooting**

### **Häufige Probleme**

| Problem | Lösung |
|---------|--------|
| **WebSocket-Verbindung schlägt fehl** | Backend-URL und Firewall-Einstellungen prüfen |
| **Styling wird nicht angezeigt** | Tailwind CSS Build-Prozess überprüfen |
| **API-Calls schlagen fehl** | CORS-Einstellungen und Environment-Variablen prüfen |
| **Dark Mode funktioniert nicht** | Theme-Provider-Konfiguration überprüfen |

### **Debug-Commands**
```bash
# Detaillierte Build-Logs
npm run build -- --debug

# TypeScript-Checks
npm run type-check

# Linting
npm run lint -- --fix
```

## 🤝 **Contributing**

### **Development Workflow**
1. Fork das Repository
2. Feature-Branch erstellen: `git checkout -b feature/amazing-feature`
3. Commits: `git commit -m 'Add amazing feature'`
4. Push: `git push origin feature/amazing-feature`
5. Pull Request erstellen

### **Code-Standards**
- **TypeScript**: Strenge Typisierung
- **ESLint**: Code-Quality-Checks
- **Prettier**: Code-Formatierung
- **Conventional Commits**: Commit-Message-Standards

## 📄 **Lizenz**

MIT License - siehe [LICENSE](LICENSE) Datei für Details.

## 🎉 **Status**

**✅ Vollständige Frontend-Architektur erstellt**

### **Implementierte Features:**
- ✅ Next.js 14 mit App Router
- ✅ TypeScript-Konfiguration
- ✅ Tailwind CSS + shadcn/ui
- ✅ Responsive Design-System
- ✅ Dark Mode Support
- ✅ Component-Architektur
- ✅ WebSocket-Unterstützung
- ✅ JWT-Authentifizierung
- ✅ Rate-Limit-Anzeige
- ✅ Accessibility Features

### **Nächste Schritte:**
1. **Dependencies installieren**: `npm install`
2. **Backend-Integration**: API-Endpunkte konfigurieren
3. **Komponenten implementieren**: UI-Komponenten finalisieren
4. **Testing**: Unit- und Integration-Tests
5. **Deployment**: Production-Setup

---

**Markerengine Frontend** - Moderne, responsive und accessible Benutzeroberfläche für Text-Analyse und Marker-Erkennung. 🚀 