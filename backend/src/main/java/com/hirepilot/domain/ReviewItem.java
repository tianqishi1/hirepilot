package com.hirepilot.domain;

import jakarta.persistence.*;
import java.time.Instant;

@Entity
@Table(name = "review_item")
public class ReviewItem {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    public Long id;
    public Long candidateId;
    @Column(columnDefinition = "TEXT") public String proposedMessage;
    public String decision = "PENDING";   // PENDING / APPROVED / REJECTED
    @Column(columnDefinition = "TEXT") public String reviewerNote;
    public Instant createdAt = Instant.now();
    public Instant decidedAt;
}