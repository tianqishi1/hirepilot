package com.hirepilot.domain;

import jakarta.persistence.*;
import java.time.Instant;

@Entity
@Table(name = "chat_message", uniqueConstraints = @UniqueConstraint(columnNames = {"idempotencyKey"}))
public class ChatMessage {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    public Long id;
    public Long candidateId;
    public String direction;              // IN / OUT
    @Column(columnDefinition = "TEXT") public String content;
    public String intent;
    @Column(length = 80) public String idempotencyKey;
    public Instant createdAt = Instant.now();
}