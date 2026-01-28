# DevOps Info Service (Java / Spring Boot)

## Overview

This Java service implements a DevOps info API using Spring Boot framework. It provides system information, service metadata, and health check endpoints in a structured JSON format. Built as a modular platform for DevOps education.

## Prerequisites

- Java 21
- Apache Maven 3.6+

## Installation

Build the project: 

```bash
cd app_java
mvn install
```

## Running the Application

### Default Run

By default, the application runs on `0.0.0.0:8080`.

```bash
java -jar ./target/*.jar
```

### Configuration

The application can be configured using **environment variables**: 

| **Variable** | **Default** | **Description**     |
| ------------ | ----------- | ------------------- |
| `HOST`       | `0.0.0.0`   | Server bind address |
| `PORT`       | `8080`      | Server port         |

## API Endpoints

### GET `/`

Returns comprehensive JSON metadata with the following top-level sections:

- **service** – name, version, description, framework
- **system** – hostname, platform, platform_version, architecture, cpu_count, python_version
- **runtime** – uptime_seconds, uptime_human, current_time, timezone
- **request** – client_ip, user_agent, method, path
- **endpoints** – list of available paths and their purpose

### GET `/health`

Returns a compact health status document:

- **status** – string status 
- **timestamp** – current UTC timestamp
- **uptime_seconds** – number of seconds the process has been running