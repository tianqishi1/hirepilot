package com.hirepilot.api;

import com.hirepilot.domain.*;
import com.hirepilot.repo.*;
import com.hirepilot.service.WorkflowService;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.server.ResponseStatusException;

import java.time.Instant;
import java.util.*;

@RestController
@RequestMapping("/api/worker")
public class WorkerController {
    private final TaskRunRepo tasks;
    private final IncidentRepo incidents;
    private final CandidateRepo candidates;
    private final ReviewRepo reviews;
    private final WorkflowService workflow;

    public WorkerController(TaskRunRepo t, IncidentRepo i, CandidateRepo c, ReviewRepo r, WorkflowService w) {
        tasks = t; incidents = i; candidates = c; reviews = r; workflow = w;
    }

    @PostMapping("/tasks/claim")
    public synchronized TaskRun claim(@RequestBody Map<String, Object> body) {
        Long jobId = ((Number) body.get("jobId")).longValue();
        for (TaskRun t : tasks.findByJobIdAndState(jobId, "RUNNING")) {
            if (t.heartbeatAt.isAfter(Instant.now().minusSeconds(90)))
                throw new ResponseStatusException(HttpStatus.CONFLICT, "该职位已有活跃任务在执行: " + t.id);
            t.state = "FAILED"; t.finishedAt = Instant.now(); tasks.save(t);   // 回收僵尸任务
        }
        TaskRun t = new TaskRun();
        t.jobId = jobId;
        t.workerId = (String) body.getOrDefault("workerId", "worker-1");
        return tasks.save(t);
    }

    @PostMapping("/tasks/{id}/heartbeat")
    public TaskRun heartbeat(@PathVariable Long id) {
        TaskRun t = tasks.findById(id).orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND));
        t.heartbeatAt = Instant.now();
        return tasks.save(t);
    }

    @PostMapping("/tasks/{id}/finish")
    public TaskRun finish(@PathVariable Long id, @RequestBody Map<String, Object> body) {
        TaskRun t = tasks.findById(id).orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND));
        t.state = (String) body.getOrDefault("state", "FINISHED");
        t.stats = String.valueOf(body.get("stats"));
        t.finishedAt = Instant.now();
        return tasks.save(t);
    }

    @PostMapping("/candidates")
    public List<Candidate> upsert(@RequestBody List<Map<String, Object>> batch) {
        List<Candidate> out = new ArrayList<>();
        for (Map<String, Object> b : batch) out.add(workflow.upsertCandidate(b));
        return out;
    }

    @PostMapping("/reviews")
    public ReviewItem createReview(@RequestBody Map<String, Object> body) {
        return workflow.createReview(((Number) body.get("candidateId")).longValue(), (String) body.get("proposedMessage"));
    }

    @GetMapping("/approved")
    public List<Map<String, Object>> approved(@RequestParam Long jobId) {
        List<Map<String, Object>> out = new ArrayList<>();
        for (Candidate c : candidates.findByJobIdAndStatus(jobId, "APPROVED")) {
            reviews.findFirstByCandidateIdAndDecisionOrderByIdDesc(c.id, "APPROVED").ifPresent(r ->
                out.add(Map.of("candidate", c, "message", r.proposedMessage)));
        }
        return out;
    }

    @PostMapping("/messages")
    public Map<String, Object> message(@RequestBody Map<String, Object> body) {
        return workflow.recordMessage(body);
    }

    @PostMapping("/escalate/{candidateId}")
    public Candidate escalate(@PathVariable Long candidateId) {
        Candidate c = candidates.findById(candidateId)
            .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND));
        return workflow.transition(c, "ESCALATED");
    }

    @PostMapping("/status")
    public Candidate setStatus(@RequestBody Map<String, Object> body) {
        Candidate c = candidates.findById(((Number) body.get("candidateId")).longValue())
            .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND));
        return workflow.transition(c, (String) body.get("status"));
    }

    @PostMapping("/incidents")
    public Incident incident(@RequestBody Incident i) { i.id = null; return incidents.save(i); }
}