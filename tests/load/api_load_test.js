// k6 Load Testing Script for Legion API
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

const errorRate = new Rate('errors');

export const options = {
  stages: [
    { duration: '2m', target: 50 },   // Ramp up to 50 users
    { duration: '5m', target: 100 },  // Ramp to 100 users
    { duration: '5m', target: 100 },  // Stay at 100 users
    { duration: '2m', target: 200 },  // Ramp to 200 users
    { duration: '3m', target: 200 },  // Stay at 200 users
    { duration: '2m', target: 0 },    // Ramp down
  ],
  thresholds: {
    'http_req_duration': ['p(95)<500', 'p(99)<1000'],  // 95% < 500ms, 99% < 1s
    'http_req_failed': ['rate<0.01'],  // Error rate < 1%
    'errors': ['rate<0.01'],
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';

export default function() {
  // Test task creation
  const createPayload = JSON.stringify({
    title: `Load Test Task ${Date.now()}`,
    description: 'Automated load testing',
    task_type: 'code_analysis',
    priority: 3
  });
  
  const createRes = http.post(
    `${BASE_URL}/api/v2/tasks`,
    createPayload,
    {
      headers: { 'Content-Type': 'application/json' },
    }
  );
  
  check(createRes, {
    'task created': (r) => r.status === 201,
    'response time OK': (r) => r.timings.duration < 500,
    'has task ID': (r) => JSON.parse(r.body).id !== undefined,
  }) || errorRate.add(1);
  
  sleep(1);
  
  // Test task listing
  const listRes = http.get(`${BASE_URL}/api/v2/tasks`);
  
  check(listRes, {
    'tasks retrieved': (r) => r.status === 200,
    'has pagination': (r) => JSON.parse(r.body).pagination !== undefined,
  }) || errorRate.add(1);
  
  sleep(1);
  
  // Test task details (if created successfully)
  if (createRes.status === 201) {
    const taskId = JSON.parse(createRes.body).id;
    const detailRes = http.get(`${BASE_URL}/api/v2/tasks/${taskId}`);
    
    check(detailRes, {
      'task details retrieved': (r) => r.status === 200,
      'correct task ID': (r) => JSON.parse(r.body).id === taskId,
    }) || errorRate.add(1);
  }
  
  sleep(2);
}

export function handleSummary(data) {
  return {
    'summary.json': JSON.stringify(data),
    stdout: textSummary(data, { indent: ' ', enableColors: true }),
  };
}
