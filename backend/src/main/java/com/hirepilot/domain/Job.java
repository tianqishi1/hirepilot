package com.hirepilot.domain;

import jakarta.persistence.*;

@Entity
@Table(name = "job")
public class Job {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    public Long id;
    public String title;
    @Column(columnDefinition = "TEXT") public String jdText;
    @Column(columnDefinition = "TEXT") public String hardFilters;   // JSON: minYears/degree/mustSkills
    @Column(columnDefinition = "TEXT") public String rubric;        // JSON: weights + rejectLine
    @Column(columnDefinition = "TEXT") public String faq;           // JSON: 常见问题标准答案
    public String greetingStyle;
    public Integer dailyLimit = 20;
    public String status = "OPEN";
}