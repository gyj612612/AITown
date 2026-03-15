# Performance Preset Guide

## Objective

Provide a simple graphics and performance policy for laptop-class hardware without making the project difficult to package or test.

## Practical Guidelines

- prefer small sprite assets and cache scaling results
- keep optional visual effects isolated from core gameplay logic
- maintain a playable fallback when optional assets are missing
- validate menu responsiveness and scene transitions on lower-end hardware

## Packaging Considerations

- avoid bundling unnecessary development environments
- keep release folders deterministic
- test packaged builds separately from the source checkout
