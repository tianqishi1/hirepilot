package com.hirepilot.api;

import com.hirepilot.domain.RunRequest;
import com.hirepilot.repo.RunRequestRepo;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.server.ResponseStatusException;

import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

@RestController
@RequestMapping("/api")
public class RunController {
    private final RunRequestRepo runs;
    private final Map<String, Instant> workerPings = new ConcurrentHashMap<>();

    public RunController(RunRequestRepo runs) { this.runs = runs; }

    @PostMapping("/runs")
    public RunRequest create(@RequestBody Map<String, Object> body) {
        Long jobId = ((Number) body.get("jobId")).longValue();
        String kind = (String) body.getOrDefault("kind", "SCREEN");
        if (!List.of("SCREEN", "ENGAGE").contains(kind))
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "kind 必须是 SCREEN 或 ENGAGE");
        if (runs.existsByJobIdAndStateIn(jobId, List.of("PENDING", "RUNNING")))
            throw new ResponseStatusException(HttpStatus.CONFLICT, "该职位已有排队/执行中的任务");
        RunRequest r = new RunRequest();
        r.jobId = jobId; r.kind = kind;
        return runs.save(r);
    }

    @GetMapping("/runs")
    public List<RunRequest> list(@RequestParam Long jobId) { return runs.findByJobIdOrderByIdDesc(jobId); }

    @PostMapping("/runs/claim")
    public synchronized ResponseEntity<RunRequest> claim() {
        return runs.findFirstByStateOrderByIdAsc("PENDING")
            .map(r -> { r.state = "RUNNING"; r.startedAt = Instant.now(); runs.save(r); return ResponseEntity.ok(r); })
            .orElseGet(() -> ResponseEntity.noContent().build());
    }

    @PostMapping("/runs/{id}/finish")
    public RunRequest finish(@PathVariable Long id, @RequestBody Map<String, Object> body) {
        RunRequest r = runs.findById(id).orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND));
        r.state = (String) body.getOrDefault("state", "DONE");
        r.stats = body.get("stats") == null ? null : String.valueOf(body.get("stats"));
        r.error = (String) body.get("error");
        r.finishedAt = Instant.now();
        return runs.save(r);
    }

    @PostMapping("/worker/ping")
    public Map<String, Object> ping(@RequestBody Map<String, String> body) {
        workerPings.put(body.getOrDefault("workerId", "worker-1"), Instant.now());
        return Map.of("ok", true);
    }

    @GetMapping("/worker/online")
    public Map<String, Object> online() {
        Instant latest = workerPings.values().stream().max(Instant::compareTo).orElse(null);
        boolean online = latest != null && latest.isAfter(Instant.now().minusSeconds(30));
        return Map.of("online", online, "lastPing", latest == null ? "" : latest.toString());
    }
}