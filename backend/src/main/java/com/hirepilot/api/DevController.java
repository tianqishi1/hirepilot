package com.hirepilot.api;

import com.hirepilot.domain.Candidate;
import com.hirepilot.repo.*;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

/** 仅开发/演示用：清空某职位的全部运行数据。生产环境应禁用或加鉴权。 */
@RestController
@RequestMapping("/api/dev")
public class DevController {
    private final CandidateRepo candidates;
    private final ReviewRepo reviews;
    private final MessageRepo messages;
    private final TaskRunRepo tasks;

    public DevController(CandidateRepo c, ReviewRepo r, MessageRepo m, TaskRunRepo t) {
        candidates = c; reviews = r; messages = m; tasks = t;
    }

    @PostMapping("/reset")
    @Transactional
    public Map<String, Object> reset(@RequestParam Long jobId) {
        List<Long> ids = candidates.findByJobId(jobId).stream().map((Candidate c) -> c.id).toList();
        if (!ids.isEmpty()) {
            messages.deleteByCandidateIdIn(ids);
            reviews.deleteByCandidateIdIn(ids);
        }
        candidates.deleteByJobId(jobId);
        tasks.deleteByJobId(jobId);
        return Map.of("ok", true, "jobId", jobId, "removedCandidates", ids.size());
    }
}