const express = require("express");
const { spawn } = require("child_process");
const cors = require("cors");
const EventEmitter = require("events");
const app = express();
const PORT = 3001;
const winston = require("winston");
const fs = require("fs");
const swaggerUi = require("swagger-ui-express");
const swaggerSpec = require("./swagger");

// Create global event emitter
const globalEmitter = new EventEmitter();

// Create logger configuration
const logger = winston.createLogger({
  level: "info",
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.printf(({ timestamp, level, message, ...meta }) => {
      const delimeter = "------";
      return `${timestamp}\n[${level.toUpperCase()}] ${message} ${
        Object.keys(meta).length ? JSON.stringify(meta, null, 2) : ""
      }\n${delimeter}`;
    })
  ),
  transports: [
    new winston.transports.File({ filename: "logs/error.log", level: "error" }),
    new winston.transports.File({ filename: "logs/combined.log" }),
    new winston.transports.Console(),
  ],
});

// Create logs directory if it doesn't exist
if (!fs.existsSync("logs")) {
  fs.mkdirSync("logs");
}

// Replace global cmdProcess with a Map to track processes by request ID
const activeProcesses = new Map();

// Handle uncaught exceptions
process.on("uncaughtException", (err) => {
  logger.error("Uncaught Exception", {
    error: err.message,
    stack: err.stack,
  });

  globalEmitter.emit("serverError", {
    type: "uncaughtException",
    error: err,
  });

  for (const [id, process] of activeProcesses) {
    process.kill();
    activeProcesses.delete(id);
  }
});

// Handle unhandled promise rejections
process.on("unhandledRejection", (reason, promise) => {
  logger.error("Unhandled Rejection", {
    reason: reason instanceof Error ? reason.message : reason,
    stack: reason instanceof Error ? reason.stack : undefined,
    promise,
  });

  globalEmitter.emit("serverError", {
    type: "unhandledRejection",
    error: reason,
  });
});

app.use(cors());

// Add swagger route (make sure this is after cors middleware)
app.use("/api-docs", swaggerUi.serve, swaggerUi.setup(swaggerSpec));

// Add swagger documentation for the stream endpoint
/**
 * @swagger
 * /stream:
 *   get:
 *     summary: Execute a command and stream its output
 *     description: Streams the stdout and stderr of a shell command to the client.
 *     parameters:
 *       - in: query
 *         name: command
 *         required: true
 *         description: The shell command to execute.
 *         schema:
 *           type: string
 *     responses:
 *       200:
 *         description: Successful operation
 *         content:
 *           text/event-stream:
 *             schema:
 *               type: string
 *       400:
 *         description: Missing or invalid query parameter
 */
app.get("/stream", (req, res) => {
  logger.debug("Request:", req.query);
  const { command: cmd } = req.query;
  const requestId = Date.now().toString(); // Generate unique ID for this request
  if (!cmd) {
    res.status(400).send("Error: 'command' query parameter is required");
    return;
  }

  const parts = cmd.split(" ");
  const command = parts[0].trim();
  const args = parts.slice(1);

  logger.debug("Command:", command);
  logger.debug("Args:", args.join(" "));

  res.setHeader("Content-Type", "text/event-stream");
  res.setHeader("Cache-Control", "no-cache");
  res.setHeader("Connection", "keep-alive");

  const cmdProcess = spawn(command, args);
  activeProcesses.set(requestId, cmdProcess);

  const sendLines = (data, type = "stdout") => {
    const lines = data.toString().split("\n");
    lines.forEach((line) => {
      if (line.trim()) {
        logger.info(`Process ${type}`, { requestId, line });
        res.write(`data: ${line}\n\n`);
      }
    });
  };

  cmdProcess.stdout.on("data", (data) => sendLines(data, "stdout"));
  cmdProcess.stderr.on("data", (data) => sendLines(data, "stderr"));

  cmdProcess.on("close", (code) => {
    res.write(`data: Process exited with code ${code}\n\n`);
    res.end();
    activeProcesses.delete(requestId);
  });

  req.on("close", () => {
    const activeProcess = activeProcesses.get(requestId);
    if (activeProcess) {
      activeProcess.kill();
      activeProcesses.delete(requestId);
    }
  });

  globalEmitter.on("serverError", (errorInfo) => {
    if (activeProcesses.has(requestId)) {
      res.write(`data: ERROR: Server Error - ${errorInfo.type}\n\n`);
      res.end();
      const process = activeProcesses.get(requestId);
      if (process) process.kill();
      activeProcesses.delete(requestId);
    }
  });
});

app.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`);
  console.log(
    `API Documentation available at http://localhost:${PORT}/api-docs`
  );
});
