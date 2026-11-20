package com.hirepilot.api;

import com.hirepilot.domain.ReviewItem;
import com.hirepilot.repo.ReviewRepo;
import com.hirepilot.service.WorkflowService;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/reviews")
public class ReviewController {
    private final ReviewRepo reviews;
    private final WorkflowService workflow;
    public ReviewController(ReviewRepo r, WorkflowService w) { reviews = r; workflow = w; }

    @GetMapping
    public List<ReviewItem> list(@RequestParam(defaultValue = "PENDING") String decision) {
        return reviews.findByDecision(decision);
    }

    @PostMapping("/{id}/approve")
    public ReviewItem approve(@PathVariable Long id, @RequestBody(required = false) Map<String, String> body) {
        body = body == null ? Map.of() : body;
        return workflow.decide(id, true, body.get("note"), body.get("message"));
    }

    @PostMapping("/{id}/reject")
    public ReviewItem reject(@PathVariable Long id, @RequestBody(required = false) Map<String, String> body) {
        body = body == null ? Map.of() : body;
        return workflow.decide(id, false, body.get("note"), null);
    }
}