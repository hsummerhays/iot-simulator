# AWS IoT Configuration Checker
# Checks certificate status, policies, things, and endpoint configuration

$ErrorActionPreference = "Stop"

# Configuration from environment variables
$CERT_ID = $env:AWS_IOT_CERT_ID
$REGION = if ($env:AWS_REGION) { $env:AWS_REGION } else { "us-east-1" }
$EXPECTED_ENDPOINT = $env:AWS_IOT_ENDPOINT

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "AWS IoT Configuration Checker" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Helper function to print results
function Print-Result ($success, $message) {
    if ($success) {
        Write-Host "  [OK] $message" -ForegroundColor Green
    }
    else {
        Write-Host "  [FAIL] $message" -ForegroundColor Red
    }
}

# 1. Check AWS CLI
Write-Host "[1/5] Checking AWS CLI..." -ForegroundColor White
if (Get-Command "aws" -ErrorAction SilentlyContinue) {
    Print-Result $true "AWS CLI is installed"
}
else {
    Print-Result $false "AWS CLI not found in PATH"
    exit 1
}

# 2. Check Certificate
Write-Host "`n[2/5] Checking Certificate..." -ForegroundColor White
try {
    $certInfo = aws iot describe-certificate --certificate-id $CERT_ID --region $REGION --output json | ConvertFrom-Json
    
    if ($certInfo.certificateDescription.status -eq "ACTIVE") {
        Print-Result $true "Certificate $CERT_ID is ACTIVE"
    }
    else {
        Print-Result $false "Certificate status is $($certInfo.certificateDescription.status)"
        Write-Host "       Run: aws iot update-certificate --certificate-id $CERT_ID --new-status ACTIVE --region $REGION" -ForegroundColor Yellow
    }
}
catch {
    Print-Result $false "Failed to find certificate: $_"
    exit 1
}

# 3. Check Policies
Write-Host "`n[3/5] Checking Policies..." -ForegroundColor White
try {
    $certArn = $certInfo.certificateDescription.certificateArn
    $policies = aws iot list-principal-policies --principal $certArn --region $REGION --output json | ConvertFrom-Json
    
    if ($policies.policies.Count -gt 0) {
        Print-Result $true "Found $($policies.policies.Count) attached policies"
        foreach ($policy in $policies.policies) {
            Write-Host "       - $($policy.policyName)" -ForegroundColor Gray
        }
    }
    else {
        Print-Result $false "No policies attached to certificate"
        Write-Host "       Fix: Attach a policy with iot:Connect, iot:Publish, iot:Subscribe, iot:Receive permissions." -ForegroundColor Yellow
    }
}
catch {
    Print-Result $false "Failed to list policies: $_"
}

# 4. Check Things
Write-Host "`n[4/5] Checking Things..." -ForegroundColor White
try {
    $things = aws iot list-principal-things --principal $certArn --region $REGION --output json | ConvertFrom-Json
    
    if ($things.things.Count -gt 0) {
        Print-Result $true "Certificate is attached to thing(s): $($things.things -join ', ')"
    }
    else {
        Print-Result $false "Certificate is NOT attached to any Thing"
        Write-Host "       Fix: Attach certificate to your IoT Thing." -ForegroundColor Yellow
    }
}
catch {
    Print-Result $false "Failed to list things: $_"
}

# 5. Check Endpoint
Write-Host "`n[5/5] Checking Endpoint..." -ForegroundColor White
try {
    $endpoint = aws iot describe-endpoint --endpoint-type iot:Data-ATS --region $REGION --output json | ConvertFrom-Json
    
    if ($endpoint.endpointAddress -eq $EXPECTED_ENDPOINT) {
        Print-Result $true "Endpoint matches configuration"
    }
    else {
        Print-Result $false "Endpoint Mismatch"
        Write-Host "       Expected: $EXPECTED_ENDPOINT" -ForegroundColor Red
        Write-Host "       Actual:   $($endpoint.endpointAddress)" -ForegroundColor Red
        Write-Host "       Fix: Update 'ENDPOINT' in simulator.py" -ForegroundColor Yellow
    }
}
catch {
    Print-Result $false "Failed to get endpoint: $_"
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Done" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan
