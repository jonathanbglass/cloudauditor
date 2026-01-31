# Python 3.14 Upgrade Assessment for CloudAuditor

**Assessment Date:** January 31, 2026  
**Current Python Version:** 3.6.5 (per `pyvenv.cfg`)  
**System Python Version:** 3.13.3  
**Target Version:** Python 3.14

## Executive Summary

The CloudAuditor codebase requires **moderate effort** to upgrade to Python 3.14. The primary issues are **legacy Python 2 syntax** that must be fixed before the code will run on Python 3.14. The good news is that AWS Lambda officially supports Python 3.14 as of November 18, 2025, and all third-party dependencies are compatible.

> [!IMPORTANT]
> **Critical Finding:** The codebase contains Python 2 syntax that will cause immediate failures on Python 3.14. These must be fixed before deployment.

## Current State Analysis

### 1. Python Version Gap

- **Current:** Python 3.6.5 (released December 2016, **EOL December 2021**)
- **Target:** Python 3.14 (released October 7, 2025)
- **Gap:** 8 major versions spanning ~9 years

This is a significant jump that requires careful testing and validation.

### 2. Code Compatibility Issues

#### 🔴 **CRITICAL: Python 2 Exception Syntax**

The following files use deprecated Python 2 exception handling syntax that **will not work** in Python 3:

**[manager.py](file:///c:/Users/jonat/GitHub/cloudauditor/manager.py)**
- Line 14: `except psycopg2.DatabaseError, exception:`
- Line 23: `except psycopg2.DatabaseError, exception:`
- Line 43: `except psycopg2.DatabaseError, exception:`

**[processor.py](file:///c:/Users/jonat/GitHub/cloudauditor/processor.py)**
- Line 19: `except psycopg2.DatabaseError, exception:`
- Line 32: `except psycopg2.DatabaseError, exception:`
- Line 111: `except psycopg2.DatabaseError, exception:`

**Required Fix:** Change `except Exception, var:` to `except Exception as var:`

#### 🔴 **CRITICAL: Python 2 Print Statements**

**[process_instances.py](file:///c:/Users/jonat/GitHub/cloudauditor/process_instances.py)**
- Line 15: `print "Processing "+str(c)+" Instances"`
- Line 32: `print "Processing "+str(len(tags))+" Instance Tags"`
- Line 45: `print z`

**Required Fix:** Convert to Python 3 print function syntax: `print("...")`

#### 🟡 **WARNING: Bare Except Clauses**

Multiple files use bare `except:` clauses which are discouraged but still functional:
- [auditor.py](file:///c:/Users/jonat/GitHub/cloudauditor/auditor.py#L95)
- [processor.py](file:///c:/Users/jonat/GitHub/cloudauditor/processor.py#L105)
- [process_instances.py](file:///c:/Users/jonat/GitHub/cloudauditor/process_instances.py#L44)

**Recommendation:** Replace with `except Exception as e:` for better error handling.

#### 🟡 **WARNING: Unnecessary Semicolons**

Several files use trailing semicolons (Python 2 style):
- Multiple `return;` statements throughout the codebase

**Recommendation:** Remove trailing semicolons (cosmetic issue, not breaking).

### 3. Third-Party Dependencies

The codebase uses the following third-party libraries:

| Library | Current Usage | Python 3.14 Compatible? | Notes |
|---------|---------------|-------------------------|-------|
| **boto3** | AWS SDK | ✅ Yes | Actively maintained, full Python 3.14 support |
| **psycopg2** | PostgreSQL driver | ✅ Yes | Version 2.9+ supports Python 3.14 |
| **beautifulsoup4** | HTML parsing | ✅ Yes | Version 4.12+ supports Python 3.14 |
| **requests** | HTTP library | ✅ Yes | Version 2.32+ supports Python 3.14 |

> [!NOTE]
> No dependency blockers found. All libraries have active Python 3.14 support.

### 4. AWS Lambda Runtime Support

✅ **AWS Lambda officially supports Python 3.14** as of November 18, 2025.

- Runtime identifier: `python3.14`
- Based on Amazon Linux 2023
- Supports Powertools for AWS Lambda (Python)

## Python 3.14 New Features & Opportunities

While upgrading, you can leverage these Python 3.14 enhancements:

### Performance & Efficiency
- **Incremental Garbage Collection:** Reduced pause times for large memory applications
- **Free-threaded Python:** Official support for better concurrency
- **Experimental JIT Compiler:** Potential performance improvements

### Developer Experience
- **Enhanced REPL:** Live syntax highlighting and better autocompletion
- **Improved Error Messages:** Clearer syntax and runtime errors
- **Zero-Overhead Debugging (PEP 768):** Attach debuggers to running processes

### Language Features
- **Deferred Annotation Evaluation:** No more forward reference quotes
- **Template String Literals (t-strings):** Safer string substitution
- **Flexible Exception Syntax (PEP 758):** Simplified exception handling

### Standard Library
- **Zstandard Compression:** Native `compression.zstd` module
- **Enhanced asyncio:** Better introspection capabilities
- **pathlib Enhancements:** New `copy()` and `move()` methods
- **UUID v6-8 Support:** Faster UUID generation (up to 40%)

## Upgrade Roadmap

### Phase 1: Fix Breaking Changes (Required)

1. **Fix Python 2 Exception Syntax**
   - Update all `except Exception, var:` to `except Exception as var:`
   - Files: `manager.py`, `processor.py`
   - Estimated effort: 15 minutes

2. **Fix Python 2 Print Statements**
   - Convert all print statements to print functions
   - File: `process_instances.py`
   - Estimated effort: 5 minutes

3. **Add Missing Import**
   - Add `from botocore.exceptions import ClientError` to files using `ClientError`
   - Files: `manager.py`, `processor.py`
   - Estimated effort: 5 minutes

### Phase 2: Update Dependencies (Recommended)

1. **Create requirements.txt**
   - Currently missing from the repository
   - Specify minimum versions compatible with Python 3.14:
     ```
     boto3>=1.35.0
     psycopg2-binary>=2.9.9
     beautifulsoup4>=4.12.0
     requests>=2.32.0
     ```

2. **Update Virtual Environment**
   - Recreate virtual environment with Python 3.14
   - Install updated dependencies

### Phase 3: Code Quality Improvements (Optional)

1. **Replace Bare Except Clauses**
   - Improve error handling specificity
   - Estimated effort: 30 minutes

2. **Remove Trailing Semicolons**
   - Modernize code style
   - Estimated effort: 10 minutes

3. **Leverage Type Hints**
   - Add type annotations for better IDE support
   - Take advantage of deferred annotation evaluation
   - Estimated effort: 2-4 hours

### Phase 4: Testing & Validation (Critical)

1. **Unit Testing**
   - Test all database operations with PostgreSQL
   - Test AWS API calls with boto3
   - Test cross-account role assumption

2. **Integration Testing**
   - Test Lambda functions (`manager.py`, `processor.py`)
   - Test SNS message processing
   - Test end-to-end audit workflow

3. **Lambda Deployment Testing**
   - Deploy to test environment with `python3.14` runtime
   - Verify Lambda layer compatibility
   - Test with actual AWS resources

## Risk Assessment

| Risk | Severity | Mitigation |
|------|----------|------------|
| Python 2 syntax causes runtime failures | 🔴 High | Fix all syntax issues before deployment |
| Dependency incompatibilities | 🟢 Low | All dependencies support Python 3.14 |
| Lambda runtime issues | 🟢 Low | AWS officially supports Python 3.14 |
| Database driver compatibility | 🟢 Low | psycopg2 2.9+ fully compatible |
| Breaking changes in boto3 | 🟡 Medium | Test thoroughly; boto3 maintains backward compatibility |

## Recommendations

### Immediate Actions (Before Upgrade)

1. ✅ **Fix all Python 2 syntax issues** (blocking)
2. ✅ **Create requirements.txt** with pinned versions
3. ✅ **Set up Python 3.14 development environment**
4. ✅ **Run existing tests** (if any) to establish baseline

### During Upgrade

1. ✅ **Upgrade in stages:** 3.6 → 3.8 → 3.10 → 3.12 → 3.14
   - Or jump directly to 3.14 if you have comprehensive tests
2. ✅ **Update Lambda runtime** to `python3.14`
3. ✅ **Test in non-production environment first**
4. ✅ **Monitor CloudWatch logs** for runtime errors

### Post-Upgrade

1. ✅ **Leverage Python 3.14 features** for performance gains
2. ✅ **Consider free-threaded mode** for concurrent workloads
3. ✅ **Update documentation** with new Python version requirements
4. ✅ **Establish regular dependency update schedule**

## Conclusion

**Upgrade Readiness: 🟡 READY WITH FIXES REQUIRED**

The CloudAuditor codebase can be upgraded to Python 3.14, but **critical syntax fixes are mandatory** before deployment. The upgrade path is straightforward:

1. Fix Python 2 syntax (25 minutes)
2. Update dependencies (10 minutes)
3. Test thoroughly (2-4 hours)
4. Deploy to Lambda with `python3.14` runtime

**Estimated Total Effort:** 4-6 hours including testing

The benefits of upgrading include:
- ✅ Security updates and bug fixes
- ✅ Performance improvements (GC, JIT, free-threading)
- ✅ Better developer experience (REPL, error messages)
- ✅ Access to modern Python features
- ✅ Continued AWS Lambda support

> [!CAUTION]
> **Do not deploy to production without fixing the Python 2 syntax issues.** The code will fail immediately on Python 3.14.

---

**Next Steps:** Review this assessment and decide on an upgrade timeline.
