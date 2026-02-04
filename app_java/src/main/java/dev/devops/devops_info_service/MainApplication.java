package dev.devops.devops_info_service;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.web.bind.annotation.*;
import org.springframework.http.ResponseEntity;
import org.springframework.http.HttpStatus;

import jakarta.servlet.http.HttpServletRequest;
import java.time.Duration;
import java.time.Instant;
import java.time.ZoneOffset;
import java.time.format.DateTimeFormatter;
import java.util.*;
import java.net.InetAddress;
import java.net.UnknownHostException;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

@SpringBootApplication
@RestController
public class MainApplication {
    
    private static final Logger logger = LoggerFactory.getLogger(MainApplication.class);
    private static final Instant APP_START_TIME = Instant.now();
    private static final String SERVICE_NAME = "devops-info-service";
    private static final String VERSION = "1.0.0";
    private static final String DESCRIPTION = "DevOps course info service";
    private static final String FRAMEWORK = "Spring Boot";

    private static final DateTimeFormatter ISO_FORMATTER = DateTimeFormatter
            .ofPattern("yyyy-MM-dd'T'HH:mm:ss.SSS'Z'")
            .withZone(ZoneOffset.UTC);
    
    public static void main(String[] args) {
        SpringApplication.run(MainApplication.class, args);
        logger.info("Server started successfully");
    }
    
    private Map<String, Object> getUptime() {
        Duration uptime = Duration.between(APP_START_TIME, Instant.now());
        long seconds = uptime.getSeconds();
        long hours = seconds / 3600;
        long minutes = (seconds % 3600) / 60;
        
        Map<String, Object> uptimeInfo = new LinkedHashMap<>();
        uptimeInfo.put("seconds", seconds);
        uptimeInfo.put("human", String.format("%d hour%s, %d minute%s", 
            hours, hours != 1 ? "s" : "", 
            minutes, minutes != 1 ? "s" : ""));
        
        return uptimeInfo;
    }
    
    private Map<String, Object> getSystemInfo() throws UnknownHostException {
        Map<String, Object> systemInfo = new LinkedHashMap<>();
        systemInfo.put("hostname", InetAddress.getLocalHost().getHostName());
        systemInfo.put("platform", System.getProperty("os.name"));
        systemInfo.put("platform_version", System.getProperty("os.version"));
        systemInfo.put("architecture", System.getProperty("os.arch"));
        systemInfo.put("cpu_count", Runtime.getRuntime().availableProcessors());
        systemInfo.put("java_version", System.getProperty("java.version"));
        systemInfo.put("java_vendor", System.getProperty("java.vendor"));
        
        return systemInfo;
    }
    
    @GetMapping("/")
    public ResponseEntity<Map<String, Object>> getServiceInfo(HttpServletRequest request) {
        String clientIp = getClientIp(request);
        logger.info("GET / from {}", clientIp);
        
        try {
            Map<String, Object> serviceInfo = new LinkedHashMap<>();
            serviceInfo.put("name", SERVICE_NAME);
            serviceInfo.put("version", VERSION);
            serviceInfo.put("description", DESCRIPTION);
            serviceInfo.put("framework", FRAMEWORK);
            
            Map<String, Object> uptime = getUptime();
            Map<String, Object> runtimeInfo = new LinkedHashMap<>();
            runtimeInfo.put("uptime_seconds", uptime.get("seconds"));
            runtimeInfo.put("uptime_human", uptime.get("human"));
            runtimeInfo.put("current_time", ISO_FORMATTER.format(Instant.now()));;
            runtimeInfo.put("timezone", "UTC");
            
            Map<String, Object> requestInfo = new LinkedHashMap<>();
            requestInfo.put("client_ip", clientIp);
            requestInfo.put("user_agent", request.getHeader("User-Agent") != null ? 
                request.getHeader("User-Agent") : "unknown");
            requestInfo.put("method", request.getMethod());
            requestInfo.put("path", request.getRequestURI());
            
            List<Map<String, String>> endpoints = new ArrayList<>();
            endpoints.add(Map.of(
                "path", "/",
                "method", "GET",
                "description", "Service information"
            ));
            endpoints.add(Map.of(
                "path", "/health",
                "method", "GET",
                "description", "Health check"
            ));
            
            Map<String, Object> response = new LinkedHashMap<>();
            response.put("service", serviceInfo);
            response.put("system", getSystemInfo());
            response.put("runtime", runtimeInfo);
            response.put("request", requestInfo);
            response.put("endpoints", endpoints);
            
            return ResponseEntity.ok(response);
            
        } catch (Exception e) {
            logger.error("Error getting service info", e);
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                .body(Map.of(
                    "error", "Internal Server Error",
                    "message", "Failed to retrieve service information"
                ));
        }
    }
    
    @GetMapping("/health")
    public ResponseEntity<Map<String, Object>> healthCheck() {
        logger.info("Health check requested");
        
        Map<String, Object> response = new LinkedHashMap<>();
        response.put("status", "healthy");
        response.put("timestamp", ISO_FORMATTER.format(Instant.now()));
        response.put("uptime_seconds", getUptime().get("seconds"));
        
        return ResponseEntity.ok(response);
    }
    
    @ExceptionHandler(UnknownHostException.class)
    public ResponseEntity<Map<String, String>> handleUnknownHostException(UnknownHostException e) {
        logger.error("Host resolution error", e);
        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
            .body(Map.of(
                "error", "System Error",
                "message", "Failed to retrieve system information"
            ));
    }
    
    @ExceptionHandler(Exception.class)
    public ResponseEntity<Map<String, String>> handleGenericException(Exception e) {
        logger.error("Unexpected error", e);
        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
            .body(Map.of(
                "error", "Internal Server Error",
                "message", "An unexpected error occurred"
            ));
    }
    
    private String getClientIp(HttpServletRequest request) {
        String xForwardedFor = request.getHeader("X-Forwarded-For");
        if (xForwardedFor != null && !xForwardedFor.isEmpty()) {
            return xForwardedFor.split(",")[0].trim();
        }
        return request.getRemoteAddr();
    }
}