package com.hirepilot.api;

import com.hirepilot.domain.Candidate;
import com.hirepilot.repo.CandidateRepo;
import com.hirepilot.repo.MessageRepo;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.server.ResponseStatusException;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/candidates")
public class CandidateController {
    private final CandidateRepo candidates;
    private final MessageRepo messages;
    public CandidateController(CandidateRepo c, MessageRepo m) { candidates = c; messages = m; }

    @GetMapping
    public List<Candidate> list(@RequestParam Long jobId, @RequestParam(required = false) String status) {
        return status == null ? candidates.findByJobId(jobId) : candidates.findByJobIdAndStatus(jobId, status);
    }

    @GetMapping("/{id}")
    public Map<String, Object> detail(@PathVariable Long id) {
        Candidate c = candidates.findById(id)
            .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "候选人不存在"));
        return Map.of("candidate", c, "messages", messages.findByCandidateIdOrderByIdAsc(id));
    }
}