# OpenAgents Desktop

An Electron + React desktop application with UI inspired by OpenWork, designed to connect to your FastAPI backend.

## Features

- 🖥️ **Native Desktop App** - Built with Electron for Windows and macOS
- ⚛️ **Modern React UI** - React 19 with TypeScript
- 🎨 **Beautiful Design** - TailwindCSS with custom theme system
- 🎭 **Smooth Animations** - Framer Motion for delightful interactions
- 🧩 **Accessible Components** - Radix UI primitives
- 🔌 **Backend Integration** - Connects to FastAPI backend

## Tech Stack

- **Frontend**: React 19, TypeScript, TailwindCSS
- **Desktop**: Electron 35
- **Build Tool**: Vite 6
- **UI Components**: Radix UI
- **Animations**: Framer Motion
- **State Management**: Zustand
- **Icons**: Lucide React

## Getting Started

### Prerequisites

- Node.js 20+
- npm or pnpm

### Installation

```bash
# Install dependencies
npm install

# Start development server
npm run dev
```

The Electron app will launch automatically with hot reload enabled.

### Backend Configuration

The app connects to your FastAPI backend at `http://localhost:8000` by default.

To change the backend URL, set the `VITE_API_URL` environment variable:

```bash
# .env file
VITE_API_URL=http://localhost:8000
```

## Development

```bash
# Run in development mode
npm run dev

# Build the app
npm run build

# Build for production (creates installer)
npm run electron:build
```

## Project Structure

```
openagents-desktop/
├── src/
│   ├── main/              # Electron main process
│   ├── preload/           # Electron preload script
│   └── renderer/          # React application
│       ├── components/    # UI components
│       ├── pages/         # Page components
│       ├── stores/        # Zustand stores
│       ├── lib/           # Utilities
│       └── styles/        # Global styles
├── dist/                  # Vite build output
├── dist-electron/         # Electron build output
└── release/               # Packaged installers
```

## UI Components

The app uses a custom design system with:

- **Theme**: Light mode with neutral color palette
- **Typography**: DM Sans font family (to be added)
- **Components**: Button, Card, Dialog, Input, Textarea, ScrollArea
- **Layout**: Sidebar navigation with task list

## Features

### Current

- ✅ Home page with task input
- ✅ Task execution page
- ✅ Sidebar navigation
- ✅ Task state management
- ✅ Responsive design

### Coming Soon

- ⏳ Task launcher (Cmd+K)
- ⏳ Settings dialog
- ⏳ Real-time task updates
- ⏳ Task history persistence

## License

MIT
