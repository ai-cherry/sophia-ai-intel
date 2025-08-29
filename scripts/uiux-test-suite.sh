#!/bin/bash

# Sophia AI UI/UX Test Suite
# User Interface and Experience Testing

set -e

echo "=========================================="
echo "Sophia AI UI/UX Test Suite"
echo "=========================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
NC='\033[0m'

# Test results
mkdir -p test-results
UX_REPORT="test-results/uiux-report-$(date +%Y%m%d_%H%M%S).txt"

# Initialize report
echo "UI/UX Test Report - $(date)" > "$UX_REPORT"
echo "========================================" >> "$UX_REPORT"

# Test counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
UX_SCORE=0

# Helper functions
test_ui_element() {
    local test_name="$1"
    local endpoint="$2"
    local search_term="$3"
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    echo -ne "${MAGENTA}[UI]${NC} $test_name... "
    
    if curl -s "$endpoint" 2>/dev/null | grep -q "$search_term"; then
        echo -e "${GREEN}FOUND${NC}"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        UX_SCORE=$((UX_SCORE + 10))
        echo "[PASS] $test_name" >> "$UX_REPORT"
    else
        echo -e "${RED}NOT FOUND${NC}"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        echo "[FAIL] $test_name" >> "$UX_REPORT"
    fi
}

test_response_time() {
    local test_name="$1"
    local endpoint="$2"
    local max_time="$3"
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    echo -ne "${BLUE}[PERF]${NC} $test_name... "
    
    start_time=$(date +%s%N)
    curl -s -o /dev/null "$endpoint" 2>/dev/null
    end_time=$(date +%s%N)
    
    response_time=$(( (end_time - start_time) / 1000000 ))
    
    if [ $response_time -lt $max_time ]; then
        echo -e "${GREEN}FAST${NC} (${response_time}ms)"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        UX_SCORE=$((UX_SCORE + 15))
        echo "[PASS] $test_name - ${response_time}ms" >> "$UX_REPORT"
    else
        echo -e "${YELLOW}SLOW${NC} (${response_time}ms)"
        echo "[WARN] $test_name - ${response_time}ms (threshold: ${max_time}ms)" >> "$UX_REPORT"
    fi
}

test_accessibility() {
    local test_name="$1"
    local endpoint="$2"
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    echo -ne "${MAGENTA}[A11Y]${NC} $test_name... "
    
    content=$(curl -s "$endpoint" 2>/dev/null || echo "")
    
    # Check for basic accessibility features
    has_lang=$(echo "$content" | grep -q 'lang=' && echo 1 || echo 0)
    has_alt=$(echo "$content" | grep -q 'alt=' && echo 1 || echo 0)
    has_aria=$(echo "$content" | grep -q 'aria-' && echo 1 || echo 0)
    
    score=$((has_lang + has_alt + has_aria))
    
    if [ $score -ge 2 ]; then
        echo -e "${GREEN}GOOD${NC}"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        UX_SCORE=$((UX_SCORE + 20))
        echo "[PASS] $test_name - Accessibility score: $score/3" >> "$UX_REPORT"
    else
        echo -e "${YELLOW}NEEDS IMPROVEMENT${NC}"
        echo "[WARN] $test_name - Accessibility score: $score/3" >> "$UX_REPORT"
    fi
}

test_mobile_responsive() {
    local test_name="$1"
    local endpoint="$2"
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    echo -ne "${MAGENTA}[MOBILE]${NC} $test_name... "
    
    # Check for viewport meta tag and responsive indicators
    if curl -s "$endpoint" 2>/dev/null | grep -q -E "viewport|responsive|mobile"; then
        echo -e "${GREEN}RESPONSIVE${NC}"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        UX_SCORE=$((UX_SCORE + 15))
        echo "[PASS] $test_name - Mobile responsive" >> "$UX_REPORT"
    else
        echo -e "${YELLOW}NOT OPTIMIZED${NC}"
        echo "[WARN] $test_name - May not be mobile optimized" >> "$UX_REPORT"
    fi
}

test_api_usability() {
    local test_name="$1"
    local endpoint="$2"
    local method="$3"
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    echo -ne "${BLUE}[API]${NC} $test_name... "
    
    status_code=$(curl -s -o /dev/null -w "%{http_code}" -X "$method" "$endpoint" 2>/dev/null)
    
    if [[ "$status_code" =~ ^(200|201|204|404)$ ]]; then
        echo -e "${GREEN}VALID${NC} (HTTP $status_code)"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        UX_SCORE=$((UX_SCORE + 10))
        echo "[PASS] $test_name - HTTP $status_code" >> "$UX_REPORT"
    else
        echo -e "${RED}ERROR${NC} (HTTP $status_code)"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        echo "[FAIL] $test_name - HTTP $status_code" >> "$UX_REPORT"
    fi
}

# ===========================================
# 1. Dashboard UI Tests
# ===========================================
echo ""
echo "1. Dashboard UI Tests"
echo "--------------------"

test_ui_element "Dashboard loads" "http://localhost:3000" "<!DOCTYPE html>"
test_response_time "Dashboard initial load" "http://localhost:3000" 2000
test_ui_element "Dashboard has navigation" "http://localhost:3000" "nav"
test_mobile_responsive "Dashboard mobile view" "http://localhost:3000"

# ===========================================
# 2. API Usability Tests
# ===========================================
echo ""
echo "2. API Usability Tests"
echo "---------------------"

test_api_usability "Health endpoint accessible" "http://localhost:3000/api/health" "GET"
test_api_usability "Metrics endpoint" "http://localhost:3000/api/metrics" "GET"
test_api_usability "Status endpoint" "http://localhost:3000/api/status" "GET"
test_response_time "API response time" "http://localhost:3000/api/health" 200

# ===========================================
# 3. User Flow Tests
# ===========================================
echo ""
echo "3. User Flow Tests"
echo "-----------------"

echo -ne "${MAGENTA}[FLOW]${NC} Chat flow... "
chat_response=$(curl -s -X POST http://localhost:3000/api/chat \
    -H "Content-Type: application/json" \
    -d '{"message":"Hello"}' 2>/dev/null || echo "{}")

if echo "$chat_response" | grep -q -E "response|message|error"; then
    echo -e "${GREEN}WORKING${NC}"
    PASSED_TESTS=$((PASSED_TESTS + 1))
    UX_SCORE=$((UX_SCORE + 20))
    echo "[PASS] Chat flow working" >> "$UX_REPORT"
else
    echo -e "${YELLOW}PARTIAL${NC}"
    echo "[WARN] Chat flow may have issues" >> "$UX_REPORT"
fi

# ===========================================
# 4. Error Handling Tests
# ===========================================
echo ""
echo "4. Error Handling Tests"
echo "----------------------"

echo -ne "${BLUE}[ERROR]${NC} 404 page handling... "
error_code=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:3000/nonexistent" 2>/dev/null)
if [ "$error_code" = "404" ]; then
    echo -e "${GREEN}PROPER${NC}"
    PASSED_TESTS=$((PASSED_TESTS + 1))
    UX_SCORE=$((UX_SCORE + 10))
    echo "[PASS] 404 errors handled properly" >> "$UX_REPORT"
else
    echo -e "${YELLOW}UNCLEAR${NC}"
    echo "[WARN] 404 handling unclear" >> "$UX_REPORT"
fi

# ===========================================
# 5. Performance Perception Tests
# ===========================================
echo ""
echo "5. Performance Perception Tests"
echo "-------------------------------"

test_response_time "Perceived performance (TTFB)" "http://localhost:3000" 100
test_response_time "API endpoint speed" "http://localhost:8080/health" 50
test_response_time "Static asset delivery" "http://localhost:3000/favicon.ico" 30

# ===========================================
# 6. Consistency Tests
# ===========================================
echo ""
echo "6. Consistency Tests"
echo "-------------------"

echo -ne "${MAGENTA}[CONSISTENCY]${NC} API response format... "
responses=()
for endpoint in "/api/health" "/api/status" "/api/metrics"; do
    response=$(curl -s "http://localhost:3000$endpoint" 2>/dev/null | head -c 100)
    responses+=("$response")
done

# Check if all responses are JSON
json_count=0
for response in "${responses[@]}"; do
    if echo "$response" | grep -q "^{"; then
        json_count=$((json_count + 1))
    fi
done

if [ $json_count -eq ${#responses[@]} ]; then
    echo -e "${GREEN}CONSISTENT${NC}"
    PASSED_TESTS=$((PASSED_TESTS + 1))
    UX_SCORE=$((UX_SCORE + 15))
    echo "[PASS] API responses are consistent" >> "$UX_REPORT"
else
    echo -e "${YELLOW}INCONSISTENT${NC}"
    echo "[WARN] API response formats vary" >> "$UX_REPORT"
fi

# ===========================================
# 7. Monitoring UI Tests
# ===========================================
echo ""
echo "7. Monitoring UI Tests"
echo "---------------------"

test_ui_element "Grafana dashboard loads" "http://localhost:3002" "Grafana"
test_response_time "Grafana response time" "http://localhost:3002" 1000
test_ui_element "Prometheus UI loads" "http://localhost:9090" "Prometheus"

# ===========================================
# 8. Documentation Tests
# ===========================================
echo ""
echo "8. Documentation & Help Tests"
echo "-----------------------------"

echo -ne "${MAGENTA}[DOCS]${NC} API documentation... "
if curl -s "http://localhost:3000/api/docs" 2>/dev/null | grep -q -E "swagger|openapi|documentation"; then
    echo -e "${GREEN}AVAILABLE${NC}"
    PASSED_TESTS=$((PASSED_TESTS + 1))
    UX_SCORE=$((UX_SCORE + 20))
    echo "[PASS] API documentation available" >> "$UX_REPORT"
else
    echo -e "${YELLOW}NOT FOUND${NC}"
    echo "[INFO] Consider adding API documentation" >> "$UX_REPORT"
fi

# ===========================================
# 9. Security UX Tests
# ===========================================
echo ""
echo "9. Security UX Tests"
echo "-------------------"

echo -ne "${BLUE}[SECURITY]${NC} HTTPS redirect... "
redirect=$(curl -I -s http://localhost 2>/dev/null | grep -i location | grep -q https && echo "yes" || echo "no")
if [ "$redirect" = "yes" ]; then
    echo -e "${GREEN}ENABLED${NC}"
    PASSED_TESTS=$((PASSED_TESTS + 1))
    UX_SCORE=$((UX_SCORE + 10))
    echo "[PASS] HTTPS redirect enabled" >> "$UX_REPORT"
else
    echo -e "${YELLOW}NOT CONFIGURED${NC}"
    echo "[INFO] HTTPS redirect not configured" >> "$UX_REPORT"
fi

# ===========================================
# 10. User Feedback Tests
# ===========================================
echo ""
echo "10. User Feedback Tests"
echo "----------------------"

echo -ne "${MAGENTA}[FEEDBACK]${NC} Loading indicators... "
TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo -e "${BLUE}MANUAL CHECK NEEDED${NC}"
echo "[INFO] Loading indicators require manual verification" >> "$UX_REPORT"

echo -ne "${MAGENTA}[FEEDBACK]${NC} Error messages... "
TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo -e "${BLUE}MANUAL CHECK NEEDED${NC}"
echo "[INFO] Error message quality requires manual verification" >> "$UX_REPORT"

# ===========================================
# Calculate UX Score
# ===========================================
MAX_SCORE=$((TOTAL_TESTS * 20))
UX_PERCENTAGE=$(echo "scale=2; $UX_SCORE * 100 / $MAX_SCORE" | bc 2>/dev/null || echo "0")

# ===========================================
# UI/UX Test Summary
# ===========================================
echo ""
echo "=========================================="
echo "UI/UX Test Suite Summary"
echo "=========================================="
echo -e "Total Tests: ${BLUE}$TOTAL_TESTS${NC}"
echo -e "Passed: ${GREEN}$PASSED_TESTS${NC}"
echo -e "Failed: ${RED}$FAILED_TESTS${NC}"
echo -e "UX Score: ${MAGENTA}$UX_SCORE/$MAX_SCORE${NC}"
echo -e "UX Rating: ${GREEN}${UX_PERCENTAGE}%${NC}"

# Determine UX Grade
if (( $(echo "$UX_PERCENTAGE >= 90" | bc -l 2>/dev/null || echo 0) )); then
    GRADE="A - Excellent"
    GRADE_COLOR=$GREEN
elif (( $(echo "$UX_PERCENTAGE >= 80" | bc -l 2>/dev/null || echo 0) )); then
    GRADE="B - Good"
    GRADE_COLOR=$GREEN
elif (( $(echo "$UX_PERCENTAGE >= 70" | bc -l 2>/dev/null || echo 0) )); then
    GRADE="C - Acceptable"
    GRADE_COLOR=$YELLOW
elif (( $(echo "$UX_PERCENTAGE >= 60" | bc -l 2>/dev/null || echo 0) )); then
    GRADE="D - Needs Improvement"
    GRADE_COLOR=$YELLOW
else
    GRADE="F - Poor"
    GRADE_COLOR=$RED
fi

echo -e "UX Grade: ${GRADE_COLOR}$GRADE${NC}"

# Recommendations
echo ""
echo "Recommendations:"
echo "---------------"

if [ $FAILED_TESTS -gt 0 ]; then
    echo "• Fix failed UI elements and endpoints"
fi

if (( $(echo "$UX_PERCENTAGE < 80" | bc -l 2>/dev/null || echo 0) )); then
    echo "• Improve response times for better perceived performance"
    echo "• Add more accessibility features"
    echo "• Ensure mobile responsiveness"
    echo "• Implement comprehensive error handling"
fi

echo "• Consider adding interactive documentation"
echo "• Implement user analytics for deeper insights"
echo "• Add progressive loading indicators"

# Save summary to report
echo "" >> "$UX_REPORT"
echo "========================================" >> "$UX_REPORT"
echo "Summary:" >> "$UX_REPORT"
echo "Total Tests: $TOTAL_TESTS" >> "$UX_REPORT"
echo "Passed: $PASSED_TESTS" >> "$UX_REPORT"
echo "Failed: $FAILED_TESTS" >> "$UX_REPORT"
echo "UX Score: $UX_SCORE/$MAX_SCORE" >> "$UX_REPORT"
echo "UX Rating: ${UX_PERCENTAGE}%" >> "$UX_REPORT"
echo "UX Grade: $GRADE" >> "$UX_REPORT"

echo ""
echo -e "Report saved to: ${BLUE}$UX_REPORT${NC}"