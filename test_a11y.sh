#!/bin/bash
# Check if ChatWindow.tsx has the h2 with onClick
grep -n "onClick={handleTitleClick}" frontend/src/renderer/components/ChatWindow.tsx
