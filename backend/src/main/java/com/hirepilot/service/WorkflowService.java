package com.hirepilot.service;

import com.hirepilot.domain.*;
import com.hirepilot.repo.*;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;

import java.time.Instant;
import java.util.*;

@Service
public class WorkflowService {
    private final CandidateRepo candidates;
    private final ReviewRepo reviews;
    private final MessageRepo messages;
    private final JobRepo jobs;

    public WorkflowService(CandidateRepo c, ReviewRepo r, MessageRepo m, JobRepo j) {
        candidates = c; reviews = r; messages = m; jobs = j;
    }

    private static final Map<String, Set<String>> TRANSITIONS = Map.of(
        "DISCOVERED", Set.of("SCORED", "REJECTED"),
        "SCORED", Set.of("PENDING_REVIEW", "REJECTED"),
        "PENDING_REVIEW", Set.of("APPROVED", "CLOSED"),
        "APPROVED", Set.of("GREETED", "CLOSED"),
        "GREETED", Set.of("CHATTING", "ESCALATED", "CLOSED"),
        "CHATTING", Set.of("INTERVIEW", "ESCALATED", "CLOSED"),
        "ESCALATED", Set.of("CHATTING", "CLOSED")
    );

    public Candidate transition(Candidate c, String to) {
        if (Objects.equals(c.status, to)) return c;
        Set<String> allowed = TRANSITIONS.getOrDefault(c.status, Set.of());
        if (!allowed.contains(to))
            throw new ResponseStatusException(HttpStatus.CONFLICT, "非法状态迁移: " + c.status + " -> " + to);
        c.status = to;
        c.updatedAt = Instant.now();
        return candidates.save(c);
    }

    @Transactional
    public Candidate upsertCandidate(Map<String, Object> body) {
        Long jobId = ((Number) body.get("jobId")).longValue();
        String externalId = (String) body.get("externalId");
        if (externalId == null) throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "externalId 必填");
        jobs.findById(jobId).orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "职位不存在"));
        Candidate c = candidates.findByJobIdAndExternalId(jobId, externalId).orElseGet(() -> {
            Candidate n = new Candidate();
            n.jobId = jobId; n.externalId = externalId;
            return n;
        });
        boolean isNew = c.id == null;
        if (body.get("name") != null) c.name = (String) body.get("name");
        if (body.get("resumeText") != null) c.resumeText = (String) body.get("resumeText");
        if (body.get("profile") != null) c.profile = (String) body.get("profile");
        if (body.get("score") != null) c.score = ((Number) body.get("score")).intValue();
        if (body.get("scoreReason") != null) c.scoreReason = (String) body.get("scoreReason");
        if (body.get("hardPass") != null) c.hardPass = (Boolean) body.get("hardPass");
        c.updatedAt = Instant.now();
        c = candidates.save(c);
        String target = (String) body.getOrDefault("status", "SCORED");
        if (isNew || "DISCOVERED".equals(c.status)) c = transition(c, target);
        return c;
    }

    @Transactional
    public ReviewItem createReview(Long candidateId, String proposedMessage) {
        Candidate c = candidates.findById(candidateId)
            .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "候选人不存在"));
        transition(c, "PENDING_REVIEW");
        ReviewItem r = new ReviewItem();
        r.candidateId = candidateId;
        r.proposedMessage = proposedMessage;
        return reviews.save(r);
    }

    @Transactional
    public ReviewItem decide(Long reviewId, boolean approve, String note, String rewritten) {
        ReviewItem r = reviews.findById(reviewId)
            .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "审核项不存在"));
        if (!"PENDING".equals(r.decision))
            throw new ResponseStatusException(HttpStatus.CONFLICT, "该审核项已处理");
        r.decision = approve ? "APPROVED" : "REJECTED";
        r.reviewerNote = note;
        r.decidedAt = Instant.now();
        if (approve && rewritten != null && !rewritten.isBlank()) r.proposedMessage = rewritten;
        Candidate c = candidates.findById(r.candidateId).orElseThrow();
        transition(c, approve ? "APPROVED" : "CLOSED");
        return reviews.save(r);
    }

    @Transactional
    public Map<String, Object> recordMessage(Map<String, Object> body) {
        String key = (String) body.get("idempotencyKey");
        if (key != null) {
            Optional<ChatMessage> dup = messages.findByIdempotencyKey(key);
            if (dup.isPresent()) return Map.of("duplicate", true, "message", dup.get());
        }
        Long candidateId = ((Number) body.get("candidateId")).longValue();
        Candidate c = candidates.findById(candidateId)
            .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "候选人不存在"));
        ChatMessage m = new ChatMessage();
        m.candidateId = candidateId;
        m.direction = (String) body.get("direction");
        m.content = (String) body.get("content");
        m.intent = (String) body.get("intent");
        m.idempotencyKey = key;
        m = messages.save(m);
        if ("OUT".equals(m.direction) && "APPROVED".equals(c.status)) transition(c, "GREETED");
        if ("IN".equals(m.direction) && "GREETED".equals(c.status)) transition(c, "CHATTING");
        return Map.of("duplicate", false, "message", m);
    }

    public Map<String, Object> dashboard(Long jobId) {
        Map<String, Long> funnel = new LinkedHashMap<>();
        for (String s : List.of("DISCOVERED", "SCORED", "REJECTED", "PENDING_REVIEW", "APPROVED", "GREETED", "CHATTING", "INTERVIEW", "ESCALATED", "CLOSED"))
            funnel.put(s, candidates.countByJobIdAndStatus(jobId, s));
        return Map.of("jobId", jobId, "funnel", funnel,
            "pendingReviews", reviews.findByDecision("PENDING").size());
    }
}