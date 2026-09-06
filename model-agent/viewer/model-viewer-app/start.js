#!/usr/bin/env node
"use strict";
const { execSync } = require("child_process");
const path = require("path");
const fs = require("fs");

const appDir = __dirname;
const nmPath = path.join(appDir, "node_modules");

if (!fs.existsSync(nmPath) || !fs.existsSync(path.join(nmPath, "express"))) {
  console.log("Installing dependencies...");
  try {
    execSync("npm install --production", { cwd: appDir, stdio: "inherit" });
  } catch(e) {
    console.error("npm install failed:", e.message);
    process.exit(1);
  }
}

// Now start the real server
require("./server.js");
