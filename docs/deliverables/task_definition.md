# Memory System Design Exercise

## Background

You are joining the Placer Intelligence (Pi) platform team. Pi is a generative agent that pulls from
Placer data and other sources to help users solve real-world location analytics problems.
Typical tasks include finding and analyzing POIs, benchmarking performance, generating
reports, and answering “why” questions with evidence.

## Current limitation
Our main agent currently operates without memory - each interaction starts fresh with no
context about the user or their history. This leads to repetitive Q&A, shallow personalization, and
missed opportunities to proactively help.

## Objective
Design a memory system that helps the agent understand users and organizations, recall
relevant past context, and deliver faster, more accurate, and more personalized outcomes.

## Scope

The system should leverage:
- Usage patterns and interactions within our agent
- User activity across other company platforms (e.g., Salesforce tickets, product usage)
- Both short-term (session/recent) and long-term (historical) memory

## Deliverable
1. Problem Analysis - Key challenges and optimization considerations you identified
2. Solution Options - 2-3 approaches you considered and their tradeoffs
3. Recommended Approach - Your chosen solution and rationale
4. Architecture Overview - How you'd implement this at scale
5. Code - Working code demonstrating your approach (note: our agents currently run on Anthropic)