import React, { useState, useEffect, useRef, useCallback } from 'react';
import './App.css';

const API_BASE_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

function App() {
  const [user, setUser] = useState(null);
  const [classes, setClasses] = useState([]);
  const [subjects, setSubjects] = useState([]);
  const [chapters, setChapters] = useState([]);
  const [selectedClass, setSelectedClass] = useState(null);
  const [selectedSubject, setSelectedSubject] = useState(null);
  const [selectedChapter, setSelectedChapter] = useState(null);
  const [chapterDetails, setChapterDetails] = useState(null);
  const [userProgress, setUserProgress] = useState([]);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [contentData, setContentData] = useState({
    title: '',
    content_type: 'document',
    file_path: '',
    description: ''
  });

  const titleInputRef = useRef(null);

  // Authentication functions
  const handleLogin = async (email, password) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });

      if (response.ok) {
        const data = await response.json();
        localStorage.setItem('token', data.access_token);
        setUser(data.user);
        fetchClasses();
        fetchUserProgress(data.user.id);
      } else {
        alert('Login failed. Please check your credentials.');
      }
    } catch (err) {
      alert('Network error. Please try again.');
    }
  };

  const handleSignup = async (email, password, role) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/auth/signup`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password, role }),
      });

      if (response.ok) {
        const data = await response.json();
        localStorage.setItem('token', data.access_token);
        setUser(data.user);
        fetchClasses();
        fetchUserProgress(data.user.id);
      } else {
        const errorData = await response.json();
        alert(errorData.detail || 'Signup failed');
      }
    } catch (err) {
      alert('Network error. Please try again.');
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    setUser(null);
    setClasses([]);
    setSubjects([]);
    setChapters([]);
    setSelectedClass(null);
    setSelectedSubject(null);
    setSelectedChapter(null);
    setChapterDetails(null);
    setUserProgress([]);
  };

  // Data fetching functions
  const fetchClasses = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_BASE_URL}/api/classes`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      
      if (response.ok) {
        const data = await response.json();
        setClasses(data);
      }
    } catch (err) {
      console.error('Error fetching classes:', err);
    }
  };

  const fetchSubjects = async (classId) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_BASE_URL}/api/subjects/${classId}`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      
      if (response.ok) {
        const data = await response.json();
        setSubjects(data);
      }
    } catch (err) {
      console.error('Error fetching subjects:', err);
    }
  };

  const fetchChapters = async (subjectId) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_BASE_URL}/api/chapters/${subjectId}`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      
      if (response.ok) {
        const data = await response.json();
        setChapters(data);
      }
    } catch (err) {
      console.error('Error fetching chapters:', err);
    }
  };

  const fetchChapterDetails = async (chapterId) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_BASE_URL}/api/chapter/${chapterId}`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      
      if (response.ok) {
        const data = await response.json();
        
        // Fetch content for this chapter
        const contentResponse = await fetch(`${API_BASE_URL}/api/content/${chapterId}`, {
          headers: { 'Authorization': `Bearer ${token}` },
        });
        
        if (contentResponse.ok) {
          const contentData = await contentResponse.json();
          data.content = contentData;
        }
        
        setChapterDetails(data);
      }
    } catch (err) {
      console.error('Error fetching chapter details:', err);
    }
  };

  const fetchUserProgress = async (userId) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_BASE_URL}/api/progress/${userId}`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      
      if (response.ok) {
        const data = await response.json();
        setUserProgress(data);
      }
    } catch (err) {
      console.error('Error fetching user progress:', err);
    }
  };

  // Navigation functions
  const handleClassSelect = (classData) => {
    setSelectedClass(classData);
    setSelectedSubject(null);
    setSelectedChapter(null);
    setChapterDetails(null);
    setSubjects([]);
    setChapters([]);
    fetchSubjects(classData.id);
  };

  const handleSubjectSelect = (subjectData) => {
    setSelectedSubject(subjectData);
    setSelectedChapter(null);
    setChapterDetails(null);
    setChapters([]);
    fetchChapters(subjectData.id);
  };

  const handleChapterSelect = (chapterData) => {
    setSelectedChapter(chapterData);
    fetchChapterDetails(chapterData.id);
  };

  // Progress tracking
  const markChapterComplete = async (chapterId) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_BASE_URL}/api/progress/update`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          chapter_id: chapterId,
          completed: true
        }),
      });

      if (response.ok) {
        alert('Chapter marked as complete!');
        fetchUserProgress(user.id);
      } else {
        const errorData = await response.json();
        alert(errorData.detail || 'Failed to update progress');
      }
    } catch (err) {
      alert('Network error. Please try again.');
    }
  };

  const getChapterProgress = (chapterId) => {
    return userProgress.find(p => p.chapter_id === chapterId);
  };

  // File type detection and handling
  const getFileType = (filePath) => {
    if (!filePath) return 'unknown';
    
    const path = filePath.toLowerCase();
    
    // Document formats
    if (path.endsWith('.doc') || path.endsWith('.docx')) return 'document';
    if (path.endsWith('.xls') || path.endsWith('.xlsx') || path.endsWith('.csv')) return 'spreadsheet';
    if (path.endsWith('.ppt') || path.endsWith('.pptx')) return 'presentation';
    if (path.endsWith('.pdf')) return 'pdf';
    if (path.endsWith('.jpg') || path.endsWith('.jpeg') || path.endsWith('.png') || path.endsWith('.gif') || path.endsWith('.bmp') || path.endsWith('.svg')) return 'image';
    if (path.endsWith('.mp4') || path.endsWith('.avi') || path.endsWith('.mov') || path.endsWith('.wmv') || path.endsWith('.flv') || path.endsWith('.mkv') || path.endsWith('.webm')) return 'video';
    if (path.endsWith('.mp3') || path.endsWith('.wav') || path.endsWith('.ogg') || path.endsWith('.flac')) return 'audio';
    if (path.endsWith('.htm') || path.endsWith('.html')) return 'webpage';
    if (path.endsWith('.txt')) return 'text';
    
    // Check for URLs
    if (path.startsWith('http://') || path.startsWith('https://')) return 'webpage';
    
    return 'file';
  };

  const getFileIcon = (fileType) => {
    switch(fileType) {
      case 'document': return '📄';
      case 'spreadsheet': return '📊';
      case 'presentation': return '📺';
      case 'pdf': return '📕';
      case 'image': return '🖼️';
      case 'video': return '🎥';
      case 'audio': return '🎵';
      case 'webpage': return '🌐';
      case 'text': return '📝';
      default: return '📁';
    }
  };

  const getFileColor = (fileType) => {
    switch(fileType) {
      case 'document': return 'from-blue-500 to-blue-600';
      case 'spreadsheet': return 'from-green-500 to-green-600';
      case 'presentation': return 'from-orange-500 to-orange-600';
      case 'pdf': return 'from-red-500 to-red-600';
      case 'image': return 'from-purple-500 to-purple-600';
      case 'video': return 'from-pink-500 to-pink-600';
      case 'audio': return 'from-yellow-500 to-yellow-600';
      case 'webpage': return 'from-indigo-500 to-indigo-600';
      case 'text': return 'from-gray-500 to-gray-600';
      default: return 'from-slate-500 to-slate-600';
    }
  };

  // Content opening function
  const openContent = async (contentId) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_BASE_URL}/api/content/open/${contentId}`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      
      if (response.ok) {
        const data = await response.json();
        
        if (data.type === 'url') {
          // Open URL in new tab
          window.open(data.path, '_blank');
        } else if (data.type === 'file') {
          // For local files, try to open them
          if (data.path.startsWith('http://') || data.path.startsWith('https://')) {
            window.open(data.path, '_blank');
          } else {
            // For local LAN files, construct file:// URL
            const fileUrl = `file:///${data.path.replace(/\\/g, '/')}`;
            window.open(fileUrl, '_blank');
          }
        }
      } else {
        alert('Failed to open content');
      }
    } catch (err) {
      alert('Error opening content');
    }
  };

  // Upload modal component
  const UploadModal = React.memo(() => {
    const [localData, setLocalData] = useState(contentData);
    
    useEffect(() => {
      if (showUploadModal) {
        setLocalData(contentData);
        // Focus the title input when modal opens
        setTimeout(() => {
          if (titleInputRef.current) {
            titleInputRef.current.focus();
          }
        }, 100);
      }
    }, [showUploadModal]);

    const handleLocalSubmit = useCallback(async (e) => {
      e.preventDefault();
      console.log('Form submitted with data:', localData);
      
      if (!selectedChapter) {
        alert('Please select a chapter first');
        return;
      }

      try {
        const token = localStorage.getItem('token');
        console.log('Submitting content with token:', token ? 'Present' : 'Missing');
        
        const response = await fetch(`${API_BASE_URL}/api/content/create`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({
            title: localData.title,
            content_type: localData.content_type,
            file_path: localData.file_path,
            description: localData.description,
            chapter_id: selectedChapter.id
          }),
        });

        console.log('Response status:', response.status);
        
        if (response.ok) {
          const result = await response.json();
          console.log('Success:', result);
          alert('Content added successfully!');
          setLocalData({ title: '', content_type: 'document', file_path: '', description: '' });
          setContentData({ title: '', content_type: 'document', file_path: '', description: '' });
          setShowUploadModal(false);
          // Refresh chapter details
          if (selectedChapter) {
            fetchChapterDetails(selectedChapter.id);
          }
        } else {
          const errorData = await response.json();
          console.log('Error:', errorData);
          alert(errorData.detail || 'Failed to add content');
        }
      } catch (err) {
        console.log('Network error:', err);
        alert('Network error. Please try again.');
      }
    }, [localData, selectedChapter]);

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-8 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-bold text-gray-800">📚 Add Content</h2>
            <button
              onClick={() => setShowUploadModal(false)}
              className="text-gray-500 hover:text-gray-700 text-2xl"
            >
              ×
            </button>
          </div>

          <div className="mb-6 p-4 bg-blue-50 rounded-lg">
            <p className="text-sm text-blue-800">
              📚 Adding to: <strong>{selectedChapter?.name}</strong>
            </p>
            <p className="text-xs text-blue-600 mt-1">
              {chapterDetails?.class?.name} → {chapterDetails?.subject?.name} → {selectedChapter?.name}
            </p>
          </div>

          <form onSubmit={handleLocalSubmit} className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                📝 Content Title
              </label>
              <input
                ref={titleInputRef}
                type="text"
                value={localData.title}
                onChange={(e) => setLocalData({...localData, title: e.target.value})}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-lg"
                placeholder="Enter a descriptive title"
                required
                autoComplete="off"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                📂 Content Type
              </label>
              <select
                value={localData.content_type}
                onChange={(e) => setLocalData({...localData, content_type: e.target.value})}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-lg"
              >
                <option value="document">📄 Document (DOC/DOCX)</option>
                <option value="spreadsheet">📊 Spreadsheet (XLS/XLSX)</option>
                <option value="presentation">📺 Presentation (PPT/PPTX)</option>
                <option value="pdf">📕 PDF Document</option>
                <option value="image">🖼️ Image</option>
                <option value="video">🎥 Video</option>
                <option value="audio">🎵 Audio</option>
                <option value="webpage">🌐 Web Page/URL</option>
                <option value="text">📝 Text File</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                📍 File Path or URL
              </label>
              <input
                type="text"
                value={localData.file_path}
                onChange={(e) => setLocalData({...localData, file_path: e.target.value})}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-lg"
                placeholder="Enter file path (e.g., C:\Documents\file.pdf) or URL (e.g., https://example.com)"
                required
                autoComplete="off"
              />
              <div className="mt-2 p-3 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-700">
                  <strong>💡 Examples:</strong>
                </p>
                <ul className="text-xs text-gray-600 mt-1 space-y-1">
                  <li>• Local file: <code>C:\Documents\lesson.pdf</code></li>
                  <li>• Network file: <code>\\server\share\video.mp4</code></li>
                  <li>• Web URL: <code>https://example.com/page.html</code></li>
                  <li>• YouTube: <code>https://youtube.com/watch?v=ID</code></li>
                </ul>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                📝 Description (Optional)
              </label>
              <textarea
                value={localData.description}
                onChange={(e) => setLocalData({...localData, description: e.target.value})}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-lg min-h-[100px] resize-y"
                placeholder="Enter description or notes about this content"
                autoComplete="off"
              />
            </div>

            <div className="flex gap-4">
              <button
                type="submit"
                className="flex-1 bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-3 rounded-lg text-lg font-medium transition-all duration-200 shadow-lg hover:shadow-xl"
              >
                📤 Add Content
              </button>
              <button
                type="button"
                onClick={() => setShowUploadModal(false)}
                className="flex-1 bg-gray-300 hover:bg-gray-400 text-gray-700 px-6 py-3 rounded-lg text-lg font-medium transition-all duration-200"
              >
                ❌ Cancel
              </button>
            </div>
          </form>
        </div>
      </div>
    );
  });

  // Login form component
  const LoginForm = () => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [isSignup, setIsSignup] = useState(false);
    const [role, setRole] = useState('student');

    const handleSubmit = (e) => {
      e.preventDefault();
      if (isSignup) {
        handleSignup(email, password, role);
      } else {
        handleLogin(email, password);
      }
    };

    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
        <div className="bg-white p-8 rounded-lg shadow-lg max-w-md w-full">
          <h2 className="text-2xl font-bold text-center mb-6 text-gray-800">
            📚 Enhanced E-Learning Platform
          </h2>
          
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                📧 Email
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                placeholder="Enter your email"
                required
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                🔒 Password
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                placeholder="Enter your password"
                required
              />
            </div>
            
            {isSignup && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  👤 Role
                </label>
                <select
                  value={role}
                  onChange={(e) => setRole(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                >
                  <option value="student">🎓 Student</option>
                  <option value="teacher">👨‍🏫 Teacher</option>
                  <option value="admin">⚙️ Admin</option>
                </select>
              </div>
            )}
            
            <button
              type="submit"
              className="w-full bg-indigo-600 hover:bg-indigo-700 text-white py-2 rounded-lg font-medium transition-colors duration-200"
            >
              {isSignup ? '🚀 Sign Up' : '🔑 Login'}
            </button>
          </form>
          
          <p className="mt-4 text-center text-sm text-gray-600">
            {isSignup ? 'Already have an account?' : "Don't have an account?"}
            <button
              onClick={() => setIsSignup(!isSignup)}
              className="ml-1 text-indigo-600 hover:text-indigo-800 font-medium"
            >
              {isSignup ? 'Login' : 'Sign Up'}
            </button>
          </p>
        </div>
      </div>
    );
  };

  // Check for existing token on component mount
  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      // Verify token by trying to fetch classes
      fetchClasses();
    }
  }, []);

  if (!user) {
    return <LoginForm />;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Header */}
      <header className="bg-white shadow-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center space-x-4">
              <h1 className="text-3xl font-bold text-gray-900">
                📚 Enhanced E-Learning Platform
              </h1>
            </div>
            <div className="flex items-center space-x-4">
              <div className="text-sm text-gray-600">
                Progress: {userProgress.filter(p => p.completed).length} chapters ({Math.round((userProgress.filter(p => p.completed).length / Math.max(userProgress.length, 1)) * 100)}%)
              </div>
              <div className="text-sm">
                Welcome, <span className="font-semibold">{user.email}</span>!
              </div>
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-indigo-100 text-indigo-800">
                {user.role}
              </span>
              <button
                onClick={handleLogout}
                className="bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors duration-200"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Classes Section */}
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h2 className="text-xl font-semibold mb-4 text-gray-800">🎓 Select Class</h2>
            <div className="space-y-3">
              {classes.map((cls) => (
                <button
                  key={cls.id}
                  onClick={() => handleClassSelect(cls)}
                  className={`w-full text-left p-4 rounded-lg border transition-all duration-200 ${
                    selectedClass?.id === cls.id
                      ? 'bg-indigo-50 border-indigo-200 text-indigo-800'
                      : 'bg-gray-50 border-gray-200 hover:bg-gray-100'
                  }`}
                >
                  <div className="font-medium">{cls.name}</div>
                  <div className="text-sm text-gray-600">{cls.grade}</div>
                  <div className="text-xs text-gray-500 mt-1">Grade Level {cls.grade}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Subjects Section */}
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h2 className="text-xl font-semibold mb-4 text-gray-800">📖 Select Subject</h2>
            {selectedClass ? (
              <div className="space-y-3">
                {subjects.map((subject) => (
                  <button
                    key={subject.id}
                    onClick={() => handleSubjectSelect(subject)}
                    className={`w-full text-left p-4 rounded-lg border transition-all duration-200 ${
                      selectedSubject?.id === subject.id
                        ? 'bg-green-50 border-green-200 text-green-800'
                        : 'bg-gray-50 border-gray-200 hover:bg-gray-100'
                    }`}
                  >
                    <div className="font-medium">{subject.name}</div>
                    <div className="text-sm text-gray-600">{subject.description}</div>
                  </button>
                ))}
              </div>
            ) : (
              <p className="text-gray-500 text-center py-8">
                👆 Please select a class first
              </p>
            )}
          </div>

          {/* Chapters Section */}
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h2 className="text-xl font-semibold mb-4 text-gray-800">📝 Select Chapter</h2>
            {selectedSubject ? (
              <div className="space-y-3">
                {chapters.map((chapter) => {
                  const progress = getChapterProgress(chapter.id);
                  return (
                    <button
                      key={chapter.id}
                      onClick={() => handleChapterSelect(chapter)}
                      className={`w-full text-left p-4 rounded-lg border transition-all duration-200 ${
                        selectedChapter?.id === chapter.id
                          ? 'bg-yellow-50 border-yellow-200 text-yellow-800'
                          : 'bg-gray-50 border-gray-200 hover:bg-gray-100'
                      }`}
                    >
                      <div className="flex justify-between items-start">
                        <div>
                          <div className="font-medium">{chapter.name}</div>
                          <div className="text-sm text-gray-600">{chapter.description}</div>
                        </div>
                        {progress?.completed && (
                          <span className="text-green-500 text-lg">✅</span>
                        )}
                      </div>
                    </button>
                  );
                })}
              </div>
            ) : (
              <p className="text-gray-500 text-center py-8">
                👆 Please select a subject first
              </p>
            )}
          </div>
        </div>

        {/* Chapter Details Section */}
        {selectedChapter && chapterDetails && (
          <div className="mt-8 bg-white rounded-lg shadow-lg p-6">
            <div className="flex justify-between items-start mb-6">
              <div>
                <h2 className="text-2xl font-bold text-gray-800">{selectedChapter.name}</h2>
                <p className="text-gray-600 mt-2">
                  {chapterDetails.class?.name} → {chapterDetails.subject?.name} → {selectedChapter.name}
                </p>
              </div>
              <div className="flex space-x-2">
                <button
                  onClick={() => markChapterComplete(selectedChapter.id)}
                  className="bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors duration-200"
                >
                  ✅ Mark Complete
                </button>
                <button
                  onClick={() => setShowUploadModal(true)}
                  className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors duration-200"
                >
                  📤 Add Content
                </button>
              </div>
            </div>

            <div className="mb-6">
              <h3 className="text-lg font-semibold text-gray-800 mb-2">Chapter Content</h3>
              <p className="text-gray-600">{selectedChapter.description}</p>
            </div>

            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-800">📚 Additional Content</h3>
              
              {chapterDetails.content && chapterDetails.content.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {chapterDetails.content.map((content) => {
                    const fileType = getFileType(content.file_path);
                    const fileIcon = getFileIcon(fileType);
                    const fileColor = getFileColor(fileType);
                    
                    return (
                      <div key={content.id} className="border rounded-lg p-4 hover:shadow-md transition-shadow">
                        <div className={`bg-gradient-to-r ${fileColor} rounded-lg p-4 text-white mb-3`}>
                          <div className="flex items-center space-x-3">
                            <div className="text-2xl">{fileIcon}</div>
                            <div>
                              <h4 className="font-bold text-lg">{content.title}</h4>
                              <p className="text-sm opacity-90">{fileType.toUpperCase()}</p>
                            </div>
                          </div>
                        </div>
                        
                        {content.description && (
                          <p className="text-gray-600 text-sm mb-3">{content.description}</p>
                        )}
                        
                        <div className="flex justify-between items-center">
                          <span className="text-xs text-gray-500 font-mono bg-gray-100 px-2 py-1 rounded">
                            {content.file_path}
                          </span>
                          <button
                            onClick={() => openContent(content.id)}
                            className="bg-blue-500 hover:bg-blue-600 text-white px-3 py-1 rounded text-sm font-medium transition-colors duration-200"
                          >
                            🔗 Open
                          </button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <p className="text-gray-500 text-center py-8">
                  📂 No additional content available yet
                </p>
              )}
            </div>
          </div>
        )}
      </main>

      {/* Upload Modal */}
      {showUploadModal && <UploadModal />}
    </div>
  );
}

export default App;