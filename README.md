# Real-Time Shell Command Viewer

A web-based solution to run and display real-time shell command outputs using a React frontend and a Node.js backend. The project streams shell command outputs to a web browser via Server-Sent Events (SSE), providing live updates.

## Table of Contents

- [Overview](#overview)
- [Folder Structure](#folder-structure)
- [Prerequisites](#prerequisites)
- [Getting Started](#getting-started)
  - [Setting up the Client](#setting-up-the-client)
  - [Setting up the Server](#setting-up-the-server)
- [Instructions to Run](#instructions-to-run)
- [Scripts](#scripts)
- [Contributing](#contributing)
- [License](#license)

## Overview

This project enables users to view real-time shell command outputs in a browser. It uses a Node.js server to execute shell commands and stream their outputs to a React frontend via SSE. Key features include:

- Real-time shell command output streaming
- SSE-based unidirectional communication
- Simple React UI to display logs
- Light / Dark mode

**Technologies Used**: Node.js, React, Server-Sent Events (SSE), Express.js.

## Folder Structure

```plaintext
project-root/
├── server/
│   └── server.js
└── client/
    ├── package.json
    └── src/
        └── App.js
```

## Instructions to Run

### Prerequisites

Ensure [Node.js](https://nodejs.org) (v22.3+) and npm are installed.

### Server Setup

1. Navigate to the `server` folder:
   ```bash
   cd server
   ```
2. Install dependencies:
   ```bash
   npm install express
   ```
3. Start the server:
   ```bash
   node server.js
   ```

Ensure the server runs on `http://localhost:3001`.

### Client Setup

1. Navigate to the `client` folder:
   ```bash
   cd client
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start the app:
   ```bash
   npm start
   ```

Access the app at `http://localhost:3000`.
