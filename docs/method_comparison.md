# HSTS Bypass Method Comparison

This document provides a comparison of different HSTS bypass methods and their effectiveness against various security configurations.

## Method Effectiveness Matrix

| Bypass Method | Standard HSTS | HSTS + includeSubdomains | HSTS Preloaded | Certificate Pinning |
|---------------|---------------|-------------------------|----------------|---------------------|
| Browser Cache Clearing | ✅ Effective | ✅ Effective | ❌ Not effective | ✅ Effective |
| SSLStrip (Classic) | ❌ Not effective | ❌ Not effective | ❌ Not effective | ❌ Not effective |
| SSLStrip2 with DNS | ⚠️ Limited | ❌ Not effective | ❌ Not effective | ❌ Not effective |
| Subdomain Bypass | ✅ Effective | ❌ Not effective | ❌ Not effective | ✅ Effective |
| Local Hosts File | ✅ Effective | ⚠️ Limited | ❌ Not effective | ✅ Effective |
| MITMProxy with CA | ✅ Effective | ✅ Effective | ⚠️ Limited | ❌ Not effective |

## Method Details

### 1. Browser Cache Clearing

**Approach**: Directly clearing browser HSTS cache by modifying browser files or using browser features.

**Effectiveness**: Works on most sites that aren't preloaded, but requires access to the user's browser.

**Detection**: Not detectable by the server, purely client-side.

### 2. SSLStrip (Classic)

**Approach**: Intercept HTTP traffic and prevent upgrading to HTTPS by rewriting links and redirects.

**Effectiveness**: Ineffective against HSTS as browsers enforce HTTPS regardless of the link format.

**Detection**: Modern browsers show security warnings when HSTS sites are accessed over HTTP.

### 3. SSLStrip2 with DNS Spoofing

**Approach**: Use DNS spoofing to direct traffic to a similar domain not covered by the HSTS policy.

**Effectiveness**: Can work if users don't notice the domain difference. Less effective with includeSubdomains.

**Detection**: Users may notice different domain in the address bar.

### 4. Subdomain Bypass

**Approach**: Use subdomains not covered by the HSTS policy if includeSubdomains is not set.

**Effectiveness**: Works on sites without includeSubdomains flag.

**Detection**: Users may notice the subdomain difference.

### 5. Local Hosts File Modification

**Approach**: Modify the hosts file to map the domain to a different IP address.

**Effectiveness**: Can bypass HSTS in specific circumstances but still limited by includeSubdomains and preloading.

**Detection**: Requires local access to the user's machine.

### 6. MITMProxy with Custom CA

**Approach**: Use a trusted Certificate Authority to generate valid certificates for intercepted connections.

**Effectiveness**: Effective if the CA is trusted by the browser, but fails against certificate pinning.

**Detection**: Advanced security tools can detect the certificate replacement.

## Recommendations for Protection

1. **Use HSTS Preloading**: Submit your domain to the [HSTS Preload List](https://hstspreload.org/)
2. **Enable includeSubdomains**: Protect all subdomains with the HSTS policy
3. **Implement Certificate Pinning**: Add additional layer of certificate validation
4. **Set Long max-age Values**: Use at least 31536000 seconds (1 year)
5. **Monitor for Unusual Traffic Patterns**: Detect potential MITM attempts
6. **Use Modern Security Headers**: Combine HSTS with CSP and other security headers
