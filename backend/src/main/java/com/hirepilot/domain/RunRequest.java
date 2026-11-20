package com.hirepilot.domain;

import jakarta.persistence.*;
import java.time.Instant;

@Entity
@Table(name = "run_request")
public class RunRequest {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    public Long id;
    public Long jobId;
    public String kind;                   // SCREEN(筛选) / ENGAGE(触达+应答)
    public String state = "PENDING";      // PENDING / RUNNING / DONE / FAILED
    @Column(columnDefinition = "TEXT") public String stats;
    @Column(columnDefinition = "TEXT") public String error;
    public Instant createdAt = Instant.now();
    public Instant startedAt;
    public Instant finishedAt;
}