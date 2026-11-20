package com.hirepilot.domain;

import jakarta.persistence.*;
import java.time.Instant;

@Entity
@Table(name = "task_run")
public class TaskRun {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    public Long id;
    public Long jobId;
    public String workerId;
    public String state = "RUNNING";      // RUNNING / FINISHED / FAILED
    @Column(columnDefinition = "TEXT") public String stats;        // JSON
    public Instant startedAt = Instant.now();
    public Instant heartbeatAt = Instant.now();
    public Instant finishedAt;
}