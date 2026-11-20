package com.hirepilot.api;

import com.hirepilot.domain.Job;
import com.hirepilot.repo.JobRepo;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.server.ResponseStatusException;

import java.util.List;

@RestController
@RequestMapping("/api/jobs")
public class JobController {
    private final JobRepo jobs;
    public JobController(JobRepo jobs) { this.jobs = jobs; }

    @PostMapping
    public Job create(@RequestBody Job job) { job.id = null; return jobs.save(job); }

    @GetMapping
    public List<Job> list() { return jobs.findAll(); }

    @GetMapping("/{id}")
    public Job get(@PathVariable Long id) {
        return jobs.findById(id).orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "职位不存在"));
    }
}