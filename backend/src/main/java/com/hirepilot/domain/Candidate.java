package com.hirepilot.domain;

import jakarta.persistence.*;
import java.time.Instant;

@Entity
@Table(name = "candidate", uniqueConstraints = @UniqueConstraint(columnNames = {"jobId", "externalId"}))
public class Candidate {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    public Long id;
    public Long jobId;
    public String externalId;
    public String name;
    @Column(columnDefinition = "TEXT") public String resumeText;
    @Column(columnDefinition = "TEXT") public String profile;      // JSON 结构化抽取
    public Integer score;
    @Column(columnDefinition = "TEXT") public String scoreReason;
    public Boolean hardPass;
    public String status = "DISCOVERED";
    public Instant createdAt = Instant.now();
    public Instant updatedAt = Instant.now();
}