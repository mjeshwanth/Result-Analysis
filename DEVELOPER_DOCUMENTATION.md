# Student Result Analysis System - Developer Documentation

## Table of Contents
1. [System Overview](#system-overview)
2. [Data Structure](#data-structure)
3. [API Endpoints](#api-endpoints)
4. [Data Fetching Examples](#data-fetching-examples)
5. [Multi-Semester Handling](#multi-semester-handling)
6. [Supply Results Processing](#supply-results-processing)
7. [Firebase Collections](#firebase-collections)
8. [JSON File Structure](#json-file-structure)
9. [Frontend Integration](#frontend-integration)
10. [Common Use Cases](#common-use-cases)

---

## System Overview

The Student Result Analysis System supports:
- **Multi-semester uploads** in single PDF files
- **Regular and Supply result processing** with attempt tracking
- **JSON generation** in both data and temp folders matching data folder format
- **Firebase integration** with intelligent data matching and duplicate prevention
- **JNTUK and Autonomous** university formats with automatic semester detection

### Key Features
- ✅ Multi-semester support (Semester 1-8) with automatic detection
- ✅ Supply result matching and attempt tracking
- ✅ JSON export to data folder (primary) and temp folder (backup)
- ✅ Firebase real-time updates with duplicate prevention
- ✅ Intelligent data merging and conflict resolution
- ✅ Enhanced success/failure feedback with detailed upload statistics
- ✅ Automatic semester detection from PDF content
- ✅ Subject grade extraction with fallback patterns

### Recent Improvements (August 2, 2025)
- **🔧 Fixed Parser Issues**: Enhanced autonomous parser to detect semester information from PDF content automatically
- **📁 Data Folder Priority**: JSON files are now saved to `data` folder first (primary location), then `temp` folder (backup)
- **🚫 Duplicate Prevention**: System now checks for existing records before saving to prevent duplicates
- **📊 Enhanced Feedback**: Dashboard shows detailed upload statistics including duplicates skipped, records saved, and JSON file location
- **🔄 Firebase Status Updates**: JSON files now include real-time Firebase upload status and cloud storage information
- **⚡ Better Error Handling**: Improved error messages and batch processing for large uploads
- **🚀 Performance Optimization**: Dramatically improved parsing speed with optimized regex patterns and batch processing
- **📈 Progress Tracking**: Real-time progress updates during PDF processing, Firebase uploads, and file storage
- **⏱️ Timing Analytics**: Detailed performance breakdown showing time spent on each operation

### Performance Improvements
- **Parser Speed**: 5-10x faster PDF parsing with optimized regex patterns and streamlined text extraction
- **Memory Usage**: Reduced memory footprint with batch processing and optimized data structures
- **Progress Feedback**: Real-time console updates showing processing progress for large files
- **Error Recovery**: Better error handling that continues processing even if individual records fail
- **Timeout Prevention**: Streamlined operations prevent timeouts on large PDF files

---

## Data Structure

### Student Record Schema
```json
{
  "student_id": "24B81A0101",
  "year": "2 Year",
  "semester": "Semester 1",
  "examType": "regular",
  "format": "autonomous",
  "university": "Autonomous",
  "upload_date": "2025-08-01",
  "sgpa": 7.03,
  "attempts": 1,
  "availableSemesters": ["Semester 1", "Semester 2"],
  "availableExamTypes": ["regular", "supply"],
  "uploadId": "autonomous_2_Year_Semester_1_regular_1722544260",
  "uploadedAt": "2025-08-01T21:11:00Z",
  "lastSupplyUpdate": "2025-08-02T10:30:00Z",
  "supplyExamTypes": ["supply"],
  "isSupplyOnly": false,
  "subjectGrades": [
    {
      "code": "24BS1003",
      "subject": "Communicative English",
      "grade": "D",
      "internals": 18,
      "credits": 3.0,
      "hasSupply": true,
      "supplyGrade": "B",
      "supplyInternals": 22
    }
  ]
}
```

### File Metadata Schema
```json
{
  "originalName": "1st BTech 1st Sem (CR24) Results.pdf",
  "storagePath": "results/autonomous/2 Year/multi_semester/1722544260_results.pdf",
  "fileUrl": "https://storage.googleapis.com/...",
  "fileSize": 2048576,
  "year": "2 Year",
  "semesters": ["Semester 1", "Semester 2"],
  "examTypes": ["regular", "supply"],
  "format": "autonomous",
  "uploadedAt": "2025-08-01T21:11:00Z",
  "status": "processed",
  "processed": true,
  "studentsCount": 1233
}
```

---

## API Endpoints

### 1. Upload Results
```http
POST /api/upload-result
Content-Type: multipart/form-data

Parameters:
- file: PDF file
- year: "1 Year" | "2 Year" | "3 Year" | "4 Year"
- semesters: JSON array ["Semester 1", "Semester 2"]
- exam_types: JSON array ["regular", "supply"]
- format: "jntuk" | "autonomous"
- generate_json: boolean (optional, for supply)
- push_to_firebase: boolean (optional, for supply)
- track_attempts: boolean (optional, for supply)
```

**Response:**
```json
{
  "success": true,
  "message": "✅ File processed successfully! Extracted 1233 student records. 📊 Saved 1200 new records to Firebase. ⚠️ Skipped 33 duplicate records. 📁 JSON file saved to data folder: parsed_results_autonomous_regular_20250802_103000.json",
  "fileId": "autonomous_2_Year_Semester_1_regular_1722544260",
  "fileUrl": "https://storage.googleapis.com/...",
  "studentsExtracted": 1233,
  "studentsProcessed": 1200,
  "duplicatesSkipped": 33,
  "jsonGenerated": true,
  "jsonFilePath": "parsed_results_autonomous_regular_20250802_103000.json",
  "uploadStatus": "success",
  "metadata": {
    "year": "2 Year",
    "semesters": ["Semester 1"],
    "examTypes": ["regular"],
    "format": "autonomous",
    "supplyProcessing": false,
    "timestamp": 1722544260
  }
}
```

**Upload Status Values:**
- `success`: All records were processed successfully
- `partial_success`: Some records were processed, but duplicates were skipped
- `failed`: No records were processed (all were duplicates or errors occurred)

### 2. Get Student Results
```http
GET /api/student-results?year=2%20Year&semester=Semester%201&exam_type=regular&format=autonomous&student_id=24B81A0101
```

**Query Parameters:**
- `year`: Filter by academic year
- `semester`: Filter by semester
- `exam_type`: Filter by exam type
- `format`: Filter by university format
- `student_id`: Search specific student

**Response:**
```json
{
  "success": true,
  "results": [...],
  "count": 150
}
```

### 3. Get Uploaded Files
```http
GET /api/uploaded-results
```

**Response:**
```json
{
  "success": true,
  "results": [...],
  "count": 25
}
```

---

## Duplicate Prevention & Data Integrity

### How Duplicate Prevention Works
1. **Document ID Generation**: Each student record gets a unique ID: `{studentId}_{year}_{semester}_{examType}`
2. **Existence Check**: Before saving, system checks if document already exists in Firestore
3. **Skip Duplicates**: If record exists, it's skipped and counted in `duplicatesSkipped`
4. **Batch Processing**: Uses Firestore batch operations for efficient bulk uploads

### Example Duplicate Scenarios
```javascript
// These would be considered duplicates:
document_id_1 = "24B81A0101_2_Year_Semester_1_regular"
document_id_2 = "24B81A0101_2_Year_Semester_1_regular"  // Duplicate!

// These would be considered different records:
document_id_1 = "24B81A0101_2_Year_Semester_1_regular"
document_id_3 = "24B81A0101_2_Year_Semester_1_supply"   // Different exam type
document_id_4 = "24B81A0101_2_Year_Semester_2_regular"  // Different semester
```

### Data Integrity Features
- **Automatic Semester Detection**: Parser extracts semester info from PDF content
- **Subject Grade Validation**: Multiple regex patterns ensure complete subject data extraction
- **Firebase Status Tracking**: Real-time monitoring of upload success/failure rates
- **Error Recovery**: Batch operations continue even if individual records fail
- **Data Consistency**: JSON files in data folder match Firebase records exactly

### Handling Upload Results
```javascript
// Check upload success
if (response.success) {
    if (response.uploadStatus === 'success') {
        console.log(`✅ All ${response.studentsProcessed} records saved successfully`);
    } else if (response.uploadStatus === 'partial_success') {
        console.log(`⚠️ ${response.studentsProcessed} new records saved, ${response.duplicatesSkipped} duplicates skipped`);
    }
} else {
    console.log(`❌ Upload failed: ${response.message}`);
}
```

---

## Data Fetching Examples

### Fetch All Students from Specific Semester
```javascript
async function getStudentsBySemester(year, semester) {
  const params = new URLSearchParams({
    year: year,
    semester: semester
  });
  
  const response = await fetch(`/api/student-results?${params}`);
  const data = await response.json();
  
  if (data.success) {
    return data.results;
  }
  throw new Error('Failed to fetch students');
}

// Usage
const students = await getStudentsBySemester("2 Year", "Semester 1");
```

### Fetch Student with Supply Results
```javascript
async function getStudentWithSupply(studentId) {
  const params = new URLSearchParams({
    student_id: studentId
  });
  
  const response = await fetch(`/api/student-results?${params}`);
  const data = await response.json();
  
  return data.results.map(record => ({
    ...record,
    hasSupplyAttempts: record.attempts > 0,
    supplySubjects: record.subjectGrades.filter(subject => subject.hasSupply)
  }));
}
```

### Fetch All Supply Results
```javascript
async function getSupplyResults(year, semester) {
  const response = await fetch('/api/student-results');
  const data = await response.json();
  
  if (data.success) {
    return data.results.filter(student => 
      student.attempts > 0 && 
      student.year === year && 
      student.semester === semester
    );
  }
  return [];
}
```

---

## Multi-Semester Handling

### Understanding Multi-Semester Uploads
When you upload a PDF containing multiple semesters:

1. **Parser Detection**: System automatically detects different semesters within the PDF
2. **Individual Records**: Each student gets separate records per semester
3. **Metadata Tracking**: `availableSemesters` array tracks all semesters in the upload

### Fetch Students Across Multiple Semesters
```javascript
async function getStudentAcrossSemesters(studentId) {
  const params = new URLSearchParams({
    student_id: studentId
  });
  
  const response = await fetch(`/api/student-results?${params}`);
  const data = await response.json();
  
  if (data.success) {
    // Group by semester
    const semesterResults = {};
    data.results.forEach(record => {
      semesterResults[record.semester] = record;
    });
    
    return semesterResults;
  }
  return {};
}

// Usage
const studentResults = await getStudentAcrossSemesters("24B81A0101");
console.log(studentResults["Semester 1"]); // First semester results
console.log(studentResults["Semester 2"]); // Second semester results
```

### Calculate Overall Performance
```javascript
function calculateOverallPerformance(semesterResults) {
  const semesters = Object.keys(semesterResults);
  let totalCredits = 0;
  let totalGradePoints = 0;
  
  semesters.forEach(sem => {
    const result = semesterResults[sem];
    if (result.sgpa && result.subjectGrades) {
      const semCredits = result.subjectGrades.reduce((sum, subject) => 
        sum + (subject.credits || 0), 0);
      totalCredits += semCredits;
      totalGradePoints += result.sgpa * semCredits;
    }
  });
  
  return {
    overallCGPA: totalCredits > 0 ? (totalGradePoints / totalCredits).toFixed(2) : 0,
    totalSemesters: semesters.length,
    totalCredits: totalCredits
  };
}
```

---

## Supply Results Processing

### How Supply Results Work
1. **Upload Supply PDF**: Select "Supply" exam type
2. **Matching Process**: System finds existing regular results by student ID
3. **Data Merging**: Supply grades are merged with existing subject grades
4. **Attempt Tracking**: Increments attempt counter
5. **History Preservation**: Original grades are preserved alongside supply grades

### Fetch Supply History
```javascript
async function getSupplyHistory(studentId, semester) {
  const params = new URLSearchParams({
    student_id: studentId,
    semester: semester
  });
  
  const response = await fetch(`/api/student-results?${params}`);
  const data = await response.json();
  
  if (data.success && data.results.length > 0) {
    const student = data.results[0];
    
    return {
      totalAttempts: student.attempts,
      hasSupply: student.attempts > 0,
      supplySubjects: student.subjectGrades.filter(subject => subject.hasSupply),
      lastSupplyUpdate: student.lastSupplyUpdate,
      supplyExamTypes: student.supplyExamTypes || []
    };
  }
  
  return null;
}
```

### Track Grade Improvements
```javascript
function getGradeImprovements(subjectGrades) {
  return subjectGrades
    .filter(subject => subject.hasSupply)
    .map(subject => ({
      code: subject.code,
      subject: subject.subject,
      originalGrade: subject.grade,
      supplyGrade: subject.supplyGrade,
      improved: isGradeImproved(subject.grade, subject.supplyGrade)
    }));
}

function isGradeImproved(originalGrade, supplyGrade) {
  const gradeOrder = ['F', 'E', 'D', 'C', 'B', 'A', 'S'];
  return gradeOrder.indexOf(supplyGrade) > gradeOrder.indexOf(originalGrade);
}
```

---

## Firebase Collections

### Collection: `uploaded_results`
**Document ID Format**: `{format}_{year}_{semesters}_{examTypes}_{timestamp}`
**Purpose**: Track uploaded PDF files and their metadata
**Example**: `autonomous_2_Year_Semester_1_Semester_2_regular_supply_1722544260`

### Collection: `student_results`
**Document ID Format**: `{studentId}_{year}_{semester}_{examType}` or `{studentId}_{year}_{timestamp}_{format}`
**Purpose**: Store individual student academic records
**Example**: `24B81A0101_2_Year_Semester_1_regular`

### Collection: `notices`
**Document ID Format**: `{title_based_id}`
**Purpose**: Store notice board announcements
**Example**: `Mid_Term_Exam_Schedule_2025`

---

## JSON File Structure

### Generated JSON Files Location
```
Primary Location: backend/data/parsed_results_{format}_{examType}_{timestamp}.json
Backup Location:  backend/temp/parsed_results_{format}_{examType}_{timestamp}.json
```

### JSON File Format (Enhanced with Firebase Status)
```json
{
  "metadata": {
    "format": "autonomous",
    "exam_type": "regular",
    "processed_at": "2025-08-02T10:30:00.123456",
    "total_students": 1233,
    "original_filename": "1st BTech 1st Sem (CR24) Results.pdf"
  },
  "students": [
    {
      "student_id": "24B81A0101",
      "semester": "Semester 1",
      "university": "Autonomous",
      "upload_date": "2025-08-01",
      "sgpa": 7.03,
      "subjectGrades": [
        {
          "code": "24BS1003",
          "subject": "Communicative English",
          "grade": "D",
          "internals": 18,
          "credits": 3.0
        }
      ]
    }
  ],
  "firebase_status": {
    "firebase_available": true,
    "saved_count": 1200,
    "failed_count": 33,
    "errors": [],
    "firebase_error": null,
    "status": "success"
  },
  "cloud_storage": {
    "uploaded": true,
    "url": "https://storage.googleapis.com/plant-ec218.firebasestorage.app/...",
    "filename": "parsed_results_autonomous_regular_20250802_103000.json",
    "upload_completed_at": "2025-08-02T10:30:15.123456"
  }
}
```

### Reading JSON Files
```javascript
const fs = require('fs');
const path = require('path');

function readGeneratedJSON(filename) {
  const filePath = path.join(__dirname, 'temp', filename);
  
  if (fs.existsSync(filePath)) {
    const data = fs.readFileSync(filePath, 'utf8');
    return JSON.parse(data);
  }
  
  throw new Error('JSON file not found');
}

// Usage
const results = readGeneratedJSON('parsed_results_autonomous_supply_20250802_103000.json');
console.log(`Total students: ${results.metadata.total_students}`);
```

---

## Frontend Integration

### React Component Example
```jsx
import React, { useState, useEffect } from 'react';

function StudentDashboard({ studentId }) {
  const [studentData, setStudentData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStudentData();
  }, [studentId]);

  async function fetchStudentData() {
    try {
      const response = await fetch(`/api/student-results?student_id=${studentId}`);
      const data = await response.json();
      
      if (data.success) {
        // Group by semester
        const semesterData = {};
        data.results.forEach(record => {
          semesterData[record.semester] = record;
        });
        setStudentData(semesterData);
      }
    } catch (error) {
      console.error('Error fetching student data:', error);
    } finally {
      setLoading(false);
    }
  }

  if (loading) return <div>Loading...</div>;

  return (
    <div className="student-dashboard">
      <h2>Student Results: {studentId}</h2>
      {Object.entries(studentData || {}).map(([semester, data]) => (
        <div key={semester} className="semester-results">
          <h3>{semester}</h3>
          <p>SGPA: {data.sgpa}</p>
          <p>Attempts: {data.attempts}</p>
          {data.attempts > 0 && (
            <div className="supply-info">
              <h4>Supply Subjects:</h4>
              {data.subjectGrades
                .filter(subject => subject.hasSupply)
                .map(subject => (
                  <div key={subject.code}>
                    {subject.code}: {subject.grade} → {subject.supplyGrade}
                  </div>
                ))}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
```

### Upload Component Example
```jsx
function ResultUpload() {
  const [formData, setFormData] = useState({
    year: '',
    semesters: [],
    examTypes: [],
    format: 'autonomous'
  });

  async function handleUpload(file) {
    const uploadData = new FormData();
    uploadData.append('file', file);
    uploadData.append('year', formData.year);
    uploadData.append('semesters', JSON.stringify(formData.semesters));
    uploadData.append('exam_types', JSON.stringify(formData.examTypes));
    uploadData.append('format', formData.format);

    if (formData.examTypes.includes('supply')) {
      uploadData.append('generate_json', true);
      uploadData.append('push_to_firebase', true);
      uploadData.append('track_attempts', true);
    }

    const response = await fetch('/api/upload-result', {
      method: 'POST',
      body: uploadData
    });

    const result = await response.json();
    console.log('Upload result:', result);
  }

  // Component JSX...
}
```

---

## Common Use Cases

### 1. Student Portal - View Own Results
```javascript
async function getStudentPortalData(studentId) {
  const response = await fetch(`/api/student-results?student_id=${studentId}`);
  const data = await response.json();
  
  if (data.success) {
    return {
      semesters: groupBySemester(data.results),
      totalAttempts: Math.max(...data.results.map(r => r.attempts || 0)),
      overallPerformance: calculateOverallPerformance(data.results)
    };
  }
  return null;
}
```

### 2. Admin Dashboard - Semester Statistics
```javascript
async function getSemesterStatistics(year, semester) {
  const params = new URLSearchParams({ year, semester });
  const response = await fetch(`/api/student-results?${params}`);
  const data = await response.json();
  
  if (data.success) {
    const students = data.results;
    
    return {
      totalStudents: students.length,
      passCount: students.filter(s => s.sgpa >= 5.0).length,
      failCount: students.filter(s => s.sgpa < 5.0).length,
      averageSGPA: students.reduce((sum, s) => sum + s.sgpa, 0) / students.length,
      supplyStudents: students.filter(s => s.attempts > 0).length,
      gradeDistribution: calculateGradeDistribution(students)
    };
  }
  return null;
}
```

### 3. Faculty Dashboard - Subject Analysis
```javascript
async function getSubjectAnalysis(subjectCode, year, semester) {
  const params = new URLSearchParams({ year, semester });
  const response = await fetch(`/api/student-results?${params}`);
  const data = await response.json();
  
  if (data.success) {
    const subjectResults = [];
    
    data.results.forEach(student => {
      const subject = student.subjectGrades.find(s => s.code === subjectCode);
      if (subject) {
        subjectResults.push({
          studentId: student.student_id,
          grade: subject.grade,
          internals: subject.internals,
          hasSupply: subject.hasSupply,
          supplyGrade: subject.supplyGrade
        });
      }
    });
    
    return {
      totalStudents: subjectResults.length,
      gradeDistribution: calculateSubjectGradeDistribution(subjectResults),
      averageInternals: subjectResults.reduce((sum, s) => sum + s.internals, 0) / subjectResults.length,
      supplyCount: subjectResults.filter(s => s.hasSupply).length
    };
  }
  return null;
}
```

### 4. Bulk Data Export
```javascript
async function exportSemesterData(year, semester, format = 'json') {
  const params = new URLSearchParams({ year, semester });
  const response = await fetch(`/api/student-results?${params}`);
  const data = await response.json();
  
  if (data.success) {
    const exportData = {
      metadata: {
        year,
        semester,
        exportedAt: new Date().toISOString(),
        totalStudents: data.results.length
      },
      students: data.results
    };
    
    if (format === 'csv') {
      return convertToCSV(exportData.students);
    }
    
    return JSON.stringify(exportData, null, 2);
  }
  
  throw new Error('Failed to export data');
}
```

---

## Performance Optimization

### 1. Pagination for Large Datasets
```javascript
async function getStudentsPaginated(page = 1, limit = 100, filters = {}) {
  const params = new URLSearchParams({
    ...filters,
    page: page.toString(),
    limit: limit.toString()
  });
  
  // Note: You'll need to implement pagination in the backend
  const response = await fetch(`/api/student-results?${params}`);
  const data = await response.json();
  
  return {
    results: data.results,
    pagination: {
      currentPage: page,
      totalPages: Math.ceil(data.total / limit),
      totalRecords: data.total,
      hasNext: page * limit < data.total,
      hasPrev: page > 1
    }
  };
}
```

### 2. Caching Strategy
```javascript
class ResultsCache {
  constructor() {
    this.cache = new Map();
    this.cacheTimeout = 5 * 60 * 1000; // 5 minutes
  }
  
  getCacheKey(params) {
    return JSON.stringify(params);
  }
  
  get(params) {
    const key = this.getCacheKey(params);
    const cached = this.cache.get(key);
    
    if (cached && Date.now() - cached.timestamp < this.cacheTimeout) {
      return cached.data;
    }
    
    this.cache.delete(key);
    return null;
  }
  
  set(params, data) {
    const key = this.getCacheKey(params);
    this.cache.set(key, {
      data,
      timestamp: Date.now()
    });
  }
  
  async getStudentResults(params) {
    const cached = this.get(params);
    if (cached) return cached;
    
    const response = await fetch(`/api/student-results?${new URLSearchParams(params)}`);
    const data = await response.json();
    
    this.set(params, data);
    return data;
  }
}

// Usage
const cache = new ResultsCache();
const results = await cache.getStudentResults({ year: "2 Year", semester: "Semester 1" });
```

---

## Error Handling

### Robust Data Fetching
```javascript
async function fetchWithRetry(url, options = {}, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      const response = await fetch(url, options);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      return await response.json();
    } catch (error) {
      console.log(`Attempt ${i + 1} failed:`, error.message);
      
      if (i === maxRetries - 1) {
        throw error;
      }
      
      // Wait before retrying
      await new Promise(resolve => setTimeout(resolve, 1000 * (i + 1)));
    }
  }
}

// Usage
try {
  const results = await fetchWithRetry('/api/student-results?student_id=24B81A0101');
  console.log('Results:', results);
} catch (error) {
  console.error('Failed to fetch after retries:', error);
}
```

---

## Security Considerations

### 1. Input Validation
```javascript
function validateStudentId(studentId) {
  // Validate format: 10 characters, alphanumeric
  const pattern = /^[A-Z0-9]{10}$/;
  return pattern.test(studentId);
}

function validateYear(year) {
  const validYears = ["1 Year", "2 Year", "3 Year", "4 Year"];
  return validYears.includes(year);
}

function validateSemester(semester) {
  const pattern = /^Semester [1-8]$/;
  return pattern.test(semester);
}

// Usage in fetch functions
async function getStudentResults(studentId, year, semester) {
  if (!validateStudentId(studentId)) {
    throw new Error('Invalid student ID format');
  }
  
  if (!validateYear(year)) {
    throw new Error('Invalid year');
  }
  
  if (!validateSemester(semester)) {
    throw new Error('Invalid semester');
  }
  
  // Proceed with fetch...
}
```

### 2. Data Sanitization
```javascript
function sanitizeStudentData(student) {
  return {
    student_id: student.student_id,
    year: student.year,
    semester: student.semester,
    sgpa: parseFloat(student.sgpa) || 0,
    subjectGrades: student.subjectGrades?.map(subject => ({
      code: subject.code,
      subject: subject.subject,
      grade: subject.grade,
      internals: parseInt(subject.internals) || 0,
      credits: parseFloat(subject.credits) || 0
    })) || []
  };
}
```

---

This documentation provides comprehensive guidance for developers working with the Student Result Analysis System. For additional support or questions, refer to the source code in the `/backend` directory.

## Quick Start Guide (Latest Updates)

### 1. Upload a PDF File
```javascript
const formData = new FormData();
formData.append('file', pdfFile);
formData.append('year', '2 Year');
formData.append('semesters', JSON.stringify(['Semester 1']));
formData.append('exam_types', JSON.stringify(['regular']));
formData.append('format', 'autonomous');

const response = await fetch('/api/upload-result', {
    method: 'POST',
    body: formData
});

const result = await response.json();
console.log(`Uploaded: ${result.studentsProcessed} new, ${result.duplicatesSkipped} duplicates`);
```

### 2. Check Data Files
- **Primary JSON**: `backend/data/parsed_results_autonomous_regular_TIMESTAMP.json`
- **Backup JSON**: `backend/temp/parsed_results_autonomous_regular_TIMESTAMP.json`
- **Firebase Collection**: `student_results`

### 3. Fetch Student Data
```javascript
// Get specific student across all semesters
const response = await fetch('/api/student-results?student_id=24B81A0101');
const data = await response.json();

// Get all students from specific semester
const response = await fetch('/api/student-results?year=2%20Year&semester=Semester%201');
const data = await response.json();
```

### 4. Troubleshooting
- **Empty subjectGrades**: Check if PDF format matches parser expectations
- **Semester showing "Unknown"**: Parser will auto-detect or use provided semester info
- **Duplicates**: System automatically prevents duplicates based on student ID + semester + exam type
- **Firebase errors**: Check `firebase_status` section in generated JSON files

**Last Updated**: August 2, 2025
**Version**: 2.1.0 (Enhanced with duplicate prevention and data integrity features)
