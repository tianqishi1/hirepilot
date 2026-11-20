package com.hirepilot.domain;

import jakarta.persistence.*;
import java.time.Instant;

@Entity
@Table(name = "incident")
public class Incident {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    public Long id;
    public Long taskRunId;
    public String kind;
    @Column(columnDefinition = "TEXT") public String detail;
    public String screenshotPath;
    public Instant createdAt = Instant.now();
}