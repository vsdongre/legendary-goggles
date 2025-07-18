import React, { useState, useEffect, useRef, useCallback } from 'react';
import './App.css';

const API_BASE_URL = process.env.REACT_APP_BACKEND_URL;

function App() {
  const [user, setUser] = useState(null);
  const [currentView, setCurrentView] = useState('login');
  const [classes, setClasses] = useState([]);
  const [subjects, setSubjects] = useState([]);
  const [chapters, setChapters] = useState([]);
  const [selectedClass, setSelectedClass] = useState(null);
  const [selectedSubject, setSelectedSubject] = useState(null);
  const [selectedChapter, setSelectedChapter] = useState(null);
  const [chapterDetails, setChapterDetails] = useState(null);
  const [userProgress, setUserProgress] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [uploadData, setUploadData] = useState({
    title: '',
    content_type: 'text',
    content_data: ''
  });
  const [showUploadModal, setShowUploadModal] = useState(false);

  // Fix for input focus issues
  const titleInputRef = useRef(null);
  const contentInputRef = useRef(null);

  // Check for existing token on app load
  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      fetchUserInfo(token);
    }
  }, []);

  const fetchUserInfo = async (token) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/auth/user`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (response.ok) {
        const userData = await response.json();
        setUser(userData);
        setCurrentView('dashboard');
        fetchClasses();
        fetchUserProgress(userData.id);
      } else {
        localStorage.removeItem('token');
      }
    } catch (err) {
      localStorage.removeItem('token');
    }
  };

  const fetchClasses = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/classes`);
      if (response.ok) {
        const classesData = await response.json();
        setClasses(classesData);
      }
    } catch (err) {
      console.error('Error fetching classes:', err);
    }
  };

  const fetchSubjects = async (classId) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/subjects/${classId}`);
      if (response.ok) {
        const subjectsData = await response.json();
        setSubjects(subjectsData);
      }
    } catch (err) {
      console.error('Error fetching subjects:', err);
    }
  };

  const fetchChapters = async (subjectId) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/chapters/${subjectId}`);
      if (response.ok) {
        const chaptersData = await response.json();
        setChapters(chaptersData);
      }
    } catch (err) {
      console.error('Error fetching chapters:', err);
    }
  };

  const fetchChapterDetails = async (chapterId) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/chapter/${chapterId}`);
      if (response.ok) {
        const chapterData = await response.json();
        setChapterDetails(chapterData);
      }
    } catch (err) {
      console.error('Error fetching chapter details:', err);
    }
  };

  const fetchUserProgress = async (userId) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_BASE_URL}/api/progress/user/${userId}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (response.ok) {
        const progressData = await response.json();
        setUserProgress(progressData);
      }
    } catch (err) {
      console.error('Error fetching progress:', err);
    }
  };

  const handleLogin = async (email, password) => {
    setLoading(true);
    setError('');
    try {
      const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password }),
      });

      if (response.ok) {
        const data = await response.json();
        localStorage.setItem('token', data.access_token);
        setUser(data.user);
        setCurrentView('dashboard');
        fetchClasses();
        fetchUserProgress(data.user.id);
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Login failed');
      }
    } catch (err) {
      setError('Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleSignup = async (username, email, password) => {
    setLoading(true);
    setError('');
    try {
      const response = await fetch(`${API_BASE_URL}/api/auth/signup`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, email, password, role: 'student' }),
      });

      if (response.ok) {
        const data = await response.json();
        localStorage.setItem('token', data.access_token);
        setUser(data.user);
        setCurrentView('dashboard');
        fetchClasses();
        fetchUserProgress(data.user.id);
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Signup failed');
      }
    } catch (err) {
      setError('Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    setUser(null);
    setCurrentView('login');
    setClasses([]);
    setSubjects([]);
    setChapters([]);
    setSelectedClass(null);
    setSelectedSubject(null);
    setSelectedChapter(null);
    setChapterDetails(null);
    setUserProgress([]);
  };

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

  // Fix for input focus issues with useCallback to prevent re-renders
  const handleTitleChange = useCallback((e) => {
    const value = e.target.value;
    setUploadData(prev => ({...prev, title: value}));
  }, []);

  const handleContentTypeChange = useCallback((e) => {
    const value = e.target.value;
    setUploadData(prev => ({...prev, content_type: value}));
  }, []);

  const handleContentDataChange = useCallback((e) => {
    const value = e.target.value;
    setUploadData(prev => ({...prev, content_data: value}));
  }, []);

  const handleUpload = useCallback(async (e) => {
    e.preventDefault();
    if (!selectedChapter) {
      alert('Please select a chapter first');
      return;
    }

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_BASE_URL}/api/content/upload`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          chapter_id: selectedChapter.id,
          title: uploadData.title,
          content_type: uploadData.content_type,
          content_data: uploadData.content_data
        }),
      });

      if (response.ok) {
        alert('Content uploaded successfully!');
        setUploadData({ title: '', content_type: 'text', content_data: '' });
        setShowUploadModal(false);
        // Refresh chapter details
        if (selectedChapter) {
          fetchChapterDetails(selectedChapter.id);
        }
      } else {
        const errorData = await response.json();
        alert(errorData.detail || 'Upload failed');
      }
    } catch (err) {
      alert('Network error. Please try again.');
    }
  }, [selectedChapter, uploadData]);

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

  // Helper function to detect video type
  const getVideoType = (videoUrl) => {
    if (!videoUrl) return 'unknown';
    
    // Check if it's a YouTube URL
    if (videoUrl.includes('youtube.com/watch?v=') || videoUrl.includes('youtu.be/')) {
      return 'youtube';
    }
    
    // Check if it's a local file path (starts with /uploads or similar)
    if (videoUrl.startsWith('/uploads/') || videoUrl.startsWith('uploads/')) {
      return 'local';
    }
    
    // Check if it's a local file with common video extensions
    const videoExtensions = ['.mp4', '.avi', '.mov', '.wmv', '.webm', '.mkv', '.flv'];
    if (videoExtensions.some(ext => videoUrl.toLowerCase().endsWith(ext))) {
      return 'local';
    }
    
    // Default to external URL
    return 'external';
  };

  // Helper function to construct full video URL
  const getFullVideoUrl = (videoPath) => {
    if (videoPath.startsWith('http')) {
      return videoPath;
    }
    // Use the new media endpoint for local files
    return `${API_BASE_URL}/api/media/${videoPath}`;
  };

  const getChapterProgress = (chapterId) => {
    return userProgress.find(p => p.chapter_id === chapterId);
  };

  const LoginForm = () => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');

    const handleSubmit = (e) => {
      e.preventDefault();
      handleLogin(email, password);
    };

    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
        <div className="max-w-md w-full space-y-8 p-8 bg-white rounded-xl shadow-lg">
          <div>
            <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
              🎓 Enhanced E-Learning Platform
            </h2>
            <p className="mt-2 text-center text-sm text-gray-600">
              Access your personalized learning experience
            </p>
          </div>
          
          <div className="bg-blue-50 p-4 rounded-lg">
            <h3 className="font-semibold text-blue-900 mb-2">Demo Accounts:</h3>
            <div className="text-sm text-blue-800">
              <p><strong>Student:</strong> demo@example.com / Demo123!</p>
              <p><strong>Admin:</strong> admin@example.com / Admin123!</p>
            </div>
          </div>

          <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
            <div className="rounded-md shadow-sm -space-y-px">
              <div>
                <input
                  id="email"
                  name="email"
                  type="email"
                  required
                  className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-t-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm"
                  placeholder="Email address"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                />
              </div>
              <div>
                <input
                  id="password"
                  name="password"
                  type="password"
                  required
                  className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-b-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm"
                  placeholder="Password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
              </div>
            </div>

            {error && (
              <div className="text-red-600 text-sm text-center">{error}</div>
            )}

            <div>
              <button
                type="submit"
                disabled={loading}
                className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
              >
                {loading ? 'Signing in...' : 'Sign in'}
              </button>
            </div>

            <div className="text-center">
              <button
                type="button"
                onClick={() => setCurrentView('signup')}
                className="font-medium text-indigo-600 hover:text-indigo-500"
              >
                Don't have an account? Sign up
              </button>
            </div>
          </form>
        </div>
      </div>
    );
  };

  const SignupForm = () => {
    const [username, setUsername] = useState('');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');

    const handleSubmit = (e) => {
      e.preventDefault();
      handleSignup(username, email, password);
    };

    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
        <div className="max-w-md w-full space-y-8 p-8 bg-white rounded-xl shadow-lg">
          <div>
            <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
              Create your account
            </h2>
          </div>
          <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
            <div className="rounded-md shadow-sm -space-y-px">
              <div>
                <input
                  id="username"
                  name="username"
                  type="text"
                  required
                  className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-t-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm"
                  placeholder="Username"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                />
              </div>
              <div>
                <input
                  id="email"
                  name="email"
                  type="email"
                  required
                  className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm"
                  placeholder="Email address"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                />
              </div>
              <div>
                <input
                  id="password"
                  name="password"
                  type="password"
                  required
                  className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-b-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm"
                  placeholder="Password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
              </div>
            </div>

            {error && (
              <div className="text-red-600 text-sm text-center">{error}</div>
            )}

            <div>
              <button
                type="submit"
                disabled={loading}
                className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
              >
                {loading ? 'Creating account...' : 'Sign up'}
              </button>
            </div>

            <div className="text-center">
              <button
                type="button"
                onClick={() => setCurrentView('login')}
                className="font-medium text-indigo-600 hover:text-indigo-500"
              >
                Already have an account? Sign in
              </button>
            </div>
          </form>
        </div>
      </div>
    );
  };

  // Memoized Upload Modal Component to prevent re-renders
  const UploadModal = React.memo(() => {
    const [localTitle, setLocalTitle] = useState(uploadData.title);
    const [localContentType, setLocalContentType] = useState(uploadData.content_type);
    const [localContentData, setLocalContentData] = useState(uploadData.content_data);
    const [uploadMode, setUploadMode] = useState('text'); // 'text' or 'file'
    const [selectedFile, setSelectedFile] = useState(null);
    const [isUploading, setIsUploading] = useState(false);
    
    // Sync with parent state only when modal opens
    useEffect(() => {
      if (showUploadModal) {
        setLocalTitle(uploadData.title);
        setLocalContentType(uploadData.content_type);
        setLocalContentData(uploadData.content_data);
        setUploadMode('text');
        setSelectedFile(null);
        setIsUploading(false);
      }
    }, [showUploadModal]);

    const handleLocalSubmit = useCallback(async (e) => {
      e.preventDefault();
      if (!selectedChapter) {
        alert('Please select a chapter first');
        return;
      }

      setIsUploading(true);
      try {
        const token = localStorage.getItem('token');
        
        if (uploadMode === 'file' && selectedFile) {
          // Handle file upload
          const formData = new FormData();
          formData.append('file', selectedFile);
          formData.append('chapter_id', selectedChapter.id);
          formData.append('title', localTitle);
          
          const response = await fetch(`${API_BASE_URL}/api/content/upload-file`, {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${token}`
            },
            body: formData
          });
          
          if (response.ok) {
            alert('File uploaded successfully!');
          } else {
            const errorData = await response.json();
            alert(errorData.detail || 'File upload failed');
          }
        } else {
          // Handle text/URL upload
          const response = await fetch(`${API_BASE_URL}/api/content/upload`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
              chapter_id: selectedChapter.id,
              title: localTitle,
              content_type: localContentType,
              content_data: localContentData
            }),
          });

          if (response.ok) {
            alert('Content uploaded successfully!');
          } else {
            const errorData = await response.json();
            alert(errorData.detail || 'Upload failed');
          }
        }
        
        // Reset form
        setLocalTitle('');
        setLocalContentType('text');
        setLocalContentData('');
        setSelectedFile(null);
        setUploadMode('text');
        setUploadData({ title: '', content_type: 'text', content_data: '' });
        setShowUploadModal(false);
        
        // Refresh chapter details
        if (selectedChapter) {
          fetchChapterDetails(selectedChapter.id);
        }
      } catch (err) {
        alert('Network error. Please try again.');
      } finally {
        setIsUploading(false);
      }
    }, [localTitle, localContentType, localContentData, selectedChapter, uploadMode, selectedFile]);

    const handleClose = useCallback(() => {
      setShowUploadModal(false);
    }, []);

    if (!showUploadModal) return null;

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-2xl p-8 w-full max-w-2xl mx-4 max-h-[90vh] overflow-y-auto shadow-2xl">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-bold text-gray-900">📤 Upload Content</h2>
            <button
              onClick={handleClose}
              className="text-gray-500 hover:text-gray-700 text-2xl font-bold"
              type="button"
            >
              ×
            </button>
          </div>
          
          <div className="mb-6 p-4 bg-blue-50 rounded-lg">
            <p className="text-sm text-blue-800">
              📚 Uploading to: <strong>{selectedChapter?.name}</strong>
            </p>
            <p className="text-xs text-blue-600 mt-1">
              {chapterDetails?.class?.name} → {chapterDetails?.subject?.name} → {selectedChapter?.name}
            </p>
          </div>

          {/* Upload Mode Selection */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              📤 Upload Method
            </label>
            <div className="flex gap-4">
              <button
                type="button"
                onClick={() => setUploadMode('text')}
                className={`flex-1 px-4 py-2 border rounded-lg text-sm font-medium transition-all ${
                  uploadMode === 'text' 
                    ? 'bg-indigo-600 text-white border-indigo-600' 
                    : 'bg-gray-50 text-gray-700 border-gray-300 hover:bg-gray-100'
                }`}
              >
                📝 Text/URL Input
              </button>
              <button
                type="button"
                onClick={() => setUploadMode('file')}
                className={`flex-1 px-4 py-2 border rounded-lg text-sm font-medium transition-all ${
                  uploadMode === 'file' 
                    ? 'bg-indigo-600 text-white border-indigo-600' 
                    : 'bg-gray-50 text-gray-700 border-gray-300 hover:bg-gray-100'
                }`}
              >
                📁 File Upload
              </button>
            </div>
          </div>

          <form onSubmit={handleLocalSubmit} className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                📝 Content Title
              </label>
              <input
                type="text"
                value={localTitle}
                onChange={(e) => setLocalTitle(e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-lg"
                placeholder="Enter a descriptive title for your content"
                required
                autoComplete="off"
              />
            </div>

            {uploadMode === 'text' ? (
              <>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    📂 Content Type
                  </label>
                  <select
                    value={localContentType}
                    onChange={(e) => setLocalContentType(e.target.value)}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-lg"
                  >
                    <option value="text">📝 Text Content</option>
                    <option value="video">🎥 Video URL</option>
                    <option value="document">📄 Document Link</option>
                    <option value="image">🖼️ Image URL</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    📋 Content Data
                  </label>
                  <textarea
                    value={localContentData}
                    onChange={(e) => setLocalContentData(e.target.value)}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-lg min-h-[200px] resize-y"
                    placeholder={
                      localContentType === 'text' ? 
                      'Enter your text content here...' :
                      localContentType === 'video' ?
                      'Enter video URL (e.g., https://www.youtube.com/watch?v=VIDEO_ID or https://youtu.be/VIDEO_ID)' :
                      localContentType === 'document' ?
                      'Enter document URL or file path' :
                      'Enter image URL'
                    }
                    required
                    autoComplete="off"
                  />
                  {localContentType === 'video' && (
                    <div className="mt-2 p-3 bg-blue-50 rounded-lg">
                      <p className="text-sm text-blue-800">
                        📹 <strong>Video URL Tips:</strong>
                      </p>
                      <ul className="text-xs text-blue-700 mt-1 space-y-1">
                        <li>• YouTube: https://www.youtube.com/watch?v=VIDEO_ID</li>
                        <li>• YouTube Short: https://youtu.be/VIDEO_ID</li>
                        <li>• Vimeo: https://vimeo.com/VIDEO_ID</li>
                        <li>• Other video URLs should be direct links</li>
                      </ul>
                    </div>
                  )}
                </div>
              </>
            ) : (
              <>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    📁 Select File
                  </label>
                  <div className="mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-gray-300 border-dashed rounded-lg hover:border-gray-400 transition-colors">
                    <div className="space-y-1 text-center">
                      <svg className="mx-auto h-12 w-12 text-gray-400" stroke="currentColor" fill="none" viewBox="0 0 48 48">
                        <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" />
                      </svg>
                      <div className="flex text-sm text-gray-600">
                        <label className="relative cursor-pointer bg-white rounded-md font-medium text-indigo-600 hover:text-indigo-500 focus-within:outline-none focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-indigo-500">
                          <span>Upload a file</span>
                          <input
                            type="file"
                            onChange={(e) => setSelectedFile(e.target.files[0])}
                            className="sr-only"
                            accept="image/*,video/*,audio/*,.pdf,.doc,.docx,.txt,.ppt,.pptx,.xls,.xlsx"
                          />
                        </label>
                        <p className="pl-1">or drag and drop</p>
                      </div>
                      <p className="text-xs text-gray-500">
                        Videos, Images, Documents up to 100MB
                      </p>
                    </div>
                  </div>
                  {selectedFile && (
                    <div className="mt-2 p-3 bg-green-50 rounded-lg">
                      <p className="text-sm text-green-800">
                        📄 <strong>Selected:</strong> {selectedFile.name}
                      </p>
                      <p className="text-xs text-green-600">
                        Size: {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                      </p>
                    </div>
                  )}
                </div>
              </>
            )}

            <div className="flex gap-4">
              <button
                type="button"
                onClick={handleClose}
                className="flex-1 bg-gray-300 hover:bg-gray-400 text-gray-700 px-6 py-3 rounded-lg text-lg font-medium transition-all duration-200"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isUploading || (uploadMode === 'file' && !selectedFile)}
                className="flex-1 bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-3 rounded-lg text-lg font-medium transition-all duration-200 shadow-lg hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isUploading ? '⏳ Uploading...' : '📤 Upload Content'}
              </button>
            </div>
          </form>
        </div>
      </div>
    );
  });

  const Dashboard = () => {
    const completedChapters = userProgress.filter(p => p.completed).length;
    const totalChapters = userProgress.length;
    const progressPercentage = totalChapters > 0 ? (completedChapters / totalChapters) * 100 : 0;

    return (
      <div className="min-h-screen bg-gray-50">
        <nav className="bg-white shadow-sm">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between h-16">
              <div className="flex items-center">
                <h1 className="text-xl font-semibold text-gray-900">🎓 Enhanced E-Learning Platform</h1>
              </div>
              <div className="flex items-center space-x-4">
                <div className="text-sm text-gray-600">
                  Progress: {completedChapters}/{totalChapters} chapters ({Math.round(progressPercentage)}%)
                </div>
                <span className="text-gray-700">Welcome, {user.username}!</span>
                <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded text-sm">
                  {user.role}
                </span>
                <button
                  onClick={handleLogout}
                  className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-md text-sm font-medium"
                >
                  Logout
                </button>
              </div>
            </div>
          </div>
        </nav>

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Class Selection */}
            <div className="bg-white rounded-lg shadow-md p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">📚 Select Class</h2>
              <div className="space-y-2">
                {classes.map((classData) => (
                  <button
                    key={classData.id}
                    onClick={() => handleClassSelect(classData)}
                    className={`w-full text-left p-3 rounded-md border transition-all ${
                      selectedClass?.id === classData.id
                        ? 'bg-indigo-100 border-indigo-500 text-indigo-900 shadow-md'
                        : 'bg-gray-50 border-gray-200 hover:bg-gray-100 hover:border-gray-300'
                    }`}
                  >
                    <div className="font-medium">{classData.name}</div>
                    <div className="text-sm text-gray-500">{classData.description}</div>
                    <div className="text-xs text-gray-400 mt-1">Grade Level: {classData.grade_level}</div>
                  </button>
                ))}
              </div>
            </div>

            {/* Subject Selection */}
            <div className="bg-white rounded-lg shadow-md p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">📖 Select Subject</h2>
              {selectedClass ? (
                <div className="space-y-2">
                  {subjects.map((subject) => (
                    <button
                      key={subject.id}
                      onClick={() => handleSubjectSelect(subject)}
                      className={`w-full text-left p-3 rounded-md border transition-all ${
                        selectedSubject?.id === subject.id
                          ? 'bg-green-100 border-green-500 text-green-900 shadow-md'
                          : 'bg-gray-50 border-gray-200 hover:bg-gray-100 hover:border-gray-300'
                      }`}
                    >
                      <div className="font-medium">{subject.name}</div>
                      <div className="text-sm text-gray-500">{subject.description}</div>
                    </button>
                  ))}
                </div>
              ) : (
                <div className="text-center text-gray-500 py-8">
                  <p>Please select a class first</p>
                  <p className="text-sm">Choose from the classes on the left</p>
                </div>
              )}
            </div>

            {/* Chapter Selection */}
            <div className="bg-white rounded-lg shadow-md p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">📝 Select Chapter</h2>
              {selectedSubject ? (
                <div className="space-y-2">
                  {chapters.map((chapter) => {
                    const progress = getChapterProgress(chapter.id);
                    return (
                      <button
                        key={chapter.id}
                        onClick={() => handleChapterSelect(chapter)}
                        className={`w-full text-left p-3 rounded-md border transition-all ${
                          selectedChapter?.id === chapter.id
                            ? 'bg-blue-100 border-blue-500 text-blue-900 shadow-md'
                            : 'bg-gray-50 border-gray-200 hover:bg-gray-100 hover:border-gray-300'
                        }`}
                      >
                        <div className="flex justify-between items-start">
                          <div>
                            <div className="font-medium">{chapter.name}</div>
                            <div className="text-sm text-gray-500">{chapter.description}</div>
                          </div>
                          {progress && progress.completed && (
                            <div className="text-green-600 text-xs font-medium">
                              ✓ Completed
                            </div>
                          )}
                        </div>
                      </button>
                    );
                  })}
                </div>
              ) : (
                <div className="text-center text-gray-500 py-8">
                  <p>Please select a subject first</p>
                  <p className="text-sm">Choose from the subjects in the middle</p>
                </div>
              )}
            </div>
          </div>

          {/* Chapter Details */}
          {chapterDetails && (
            <div className="mt-8 bg-white rounded-lg shadow-md p-6">
              <div className="flex justify-between items-start mb-6">
                <div>
                  <h3 className="text-2xl font-bold text-gray-900 mb-2">
                    {chapterDetails.chapter.name}
                  </h3>
                  <div className="text-sm text-gray-600 mb-4">
                    {chapterDetails.class.name} → {chapterDetails.subject.name} → {chapterDetails.chapter.name}
                  </div>
                  <p className="text-gray-700 mb-4">{chapterDetails.chapter.description}</p>
                </div>
                <button
                  onClick={() => markChapterComplete(chapterDetails.chapter.id)}
                  className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-md text-sm font-medium flex items-center gap-2"
                >
                  <span>✓</span>
                  Mark Complete
                </button>
              </div>

              <div className="prose max-w-none mb-6">
                <h4 className="text-lg font-semibold text-gray-900 mb-3">Chapter Content</h4>
                <p className="text-gray-800 leading-relaxed">
                  {chapterDetails.chapter.content}
                </p>
              </div>

              {/* Additional Content */}
              {chapterDetails.content && chapterDetails.content.length > 0 && (
                <div className="mb-6">
                  <h4 className="text-lg font-semibold text-gray-900 mb-4">📎 Additional Content</h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {chapterDetails.content.map((content) => (
                      <div key={content.id} className="border rounded-lg p-4 hover:shadow-md transition-shadow">
                        <h5 className="font-medium text-gray-900 mb-2">{content.title}</h5>
                        <span className={`inline-block px-2 py-1 rounded text-sm mb-2 font-medium content-type-${content.content_type}`}>
                          {content.content_type === 'video' ? '🎥 Video' :
                           content.content_type === 'image' ? '🖼️ Image' :
                           content.content_type === 'document' ? '📄 Document' :
                           '📝 Text'}
                        </span>
                        
                        {/* Video Content */}
                        {content.content_type === 'video' ? (
                          <div className="mt-3">
                            {(() => {
                              const videoType = getVideoType(content.content_data);
                              
                              if (videoType === 'youtube') {
                                return (
                                  <div className="bg-gradient-to-r from-red-500 to-red-600 rounded-lg p-6 text-white">
                                    {/* Video Icon and Title */}
                                    <div className="flex items-center space-x-4 mb-4">
                                      <div className="w-12 h-12 bg-white bg-opacity-20 rounded-lg flex items-center justify-center text-2xl">
                                        ▶️
                                      </div>
                                      <div>
                                        <h6 className="font-bold text-lg">{content.title}</h6>
                                        <p className="text-red-100 text-sm">YouTube Video</p>
                                      </div>
                                    </div>
                                    
                                    {/* Large Watch Button */}
                                    <a 
                                      href={content.content_data} 
                                      target="_blank" 
                                      rel="noopener noreferrer" 
                                      className="block w-full bg-white text-red-600 text-center py-4 px-6 rounded-lg font-bold text-lg hover:bg-red-50 transition-colors duration-200 shadow-lg"
                                    >
                                      🎥 WATCH ON YOUTUBE
                                    </a>
                                    
                                    {/* Video URL Display */}
                                    <div className="mt-3 text-center">
                                      <p className="text-red-100 text-sm">
                                        📺 Video will open in YouTube
                                      </p>
                                      <p className="text-red-200 text-xs mt-1 break-all">
                                        {content.content_data}
                                      </p>
                                    </div>
                                    
                                    {/* Additional Actions */}
                                    <div className="mt-4 flex justify-center space-x-2">
                                      <button 
                                        onClick={() => {
                                          navigator.clipboard.writeText(content.content_data);
                                          alert('Video URL copied to clipboard!');
                                        }}
                                        className="px-4 py-2 bg-white bg-opacity-20 text-white rounded hover:bg-opacity-30 transition-colors text-sm"
                                      >
                                        📋 Copy URL
                                      </button>
                                      <button 
                                        onClick={() => {
                                          const videoId = content.content_data.includes('youtube.com/watch?v=') ? 
                                            content.content_data.split('v=')[1].split('&')[0] :
                                            content.content_data.includes('youtu.be/') ?
                                            content.content_data.split('youtu.be/')[1].split('?')[0] : null;
                                          
                                          if (videoId) {
                                            const shareUrl = `https://www.youtube.com/watch?v=${videoId}`;
                                            if (navigator.share) {
                                              navigator.share({
                                                title: content.title,
                                                url: shareUrl
                                              });
                                            } else {
                                              alert(`Share this video: ${shareUrl}`);
                                            }
                                          }
                                        }}
                                        className="px-4 py-2 bg-white bg-opacity-20 text-white rounded hover:bg-opacity-30 transition-colors text-sm"
                                      >
                                        📤 Share
                                      </button>
                                    </div>
                                  </div>
                                );
                              } else if (videoType === 'local') {
                                return (
                                  <div className="bg-gradient-to-r from-purple-500 to-purple-600 rounded-lg p-6 text-white">
                                    {/* Video Icon and Title */}
                                    <div className="flex items-center space-x-4 mb-4">
                                      <div className="w-12 h-12 bg-white bg-opacity-20 rounded-lg flex items-center justify-center text-2xl">
                                        🎬
                                      </div>
                                      <div>
                                        <h6 className="font-bold text-lg">{content.title}</h6>
                                        <p className="text-purple-100 text-sm">Local Video File</p>
                                      </div>
                                    </div>
                                    
                                    {/* Video Player */}
                                    <div className="bg-black rounded-lg overflow-hidden shadow-xl">
                                      <video 
                                        controls 
                                        className="w-full h-auto"
                                        preload="metadata"
                                        onError={(e) => {
                                          e.target.style.display = 'none';
                                          const fallbackDiv = e.target.parentElement.querySelector('.video-fallback');
                                          if (fallbackDiv) {
                                            fallbackDiv.style.display = 'block';
                                          }
                                        }}
                                      >
                                        <source src={getFullVideoUrl(content.content_data)} type="video/mp4" />
                                        <source src={getFullVideoUrl(content.content_data)} type="video/webm" />
                                        <source src={getFullVideoUrl(content.content_data)} type="video/ogg" />
                                        Your browser does not support the video tag.
                                      </video>
                                      
                                      {/* Fallback Error Message */}
                                      <div className="video-fallback hidden p-8 text-center text-white">
                                        <div className="text-6xl mb-4">❌</div>
                                        <h3 className="text-xl font-bold mb-2">Video Could Not Load</h3>
                                        <p className="text-gray-300 mb-4">There was an issue loading this video file.</p>
                                        <a 
                                          href={getFullVideoUrl(content.content_data)} 
                                          target="_blank" 
                                          rel="noopener noreferrer"
                                          className="inline-block bg-purple-600 hover:bg-purple-700 text-white px-6 py-3 rounded-lg font-medium"
                                        >
                                          🔗 Try Direct Link
                                        </a>
                                      </div>
                                    </div>
                                    
                                    {/* Video Info */}
                                    <div className="mt-4 text-center">
                                      <p className="text-purple-100 text-sm">
                                        🎥 Playing from server
                                      </p>
                                      <p className="text-purple-200 text-xs mt-1">
                                        {content.content_data}
                                      </p>
                                    </div>
                                    
                                    {/* Additional Actions */}
                                    <div className="mt-4 flex justify-center space-x-2">
                                      <a 
                                        href={getFullVideoUrl(content.content_data)} 
                                        target="_blank" 
                                        rel="noopener noreferrer"
                                        className="px-4 py-2 bg-white bg-opacity-20 text-white rounded hover:bg-opacity-30 transition-colors text-sm"
                                      >
                                        🔗 Open in New Tab
                                      </a>
                                      <a 
                                        href={getFullVideoUrl(content.content_data)} 
                                        download
                                        className="px-4 py-2 bg-white bg-opacity-20 text-white rounded hover:bg-opacity-30 transition-colors text-sm"
                                      >
                                        📥 Download
                                      </a>
                                    </div>
                                  </div>
                                );
                              } else {
                                return (
                                  <div className="bg-gradient-to-r from-blue-500 to-blue-600 rounded-lg p-6 text-white">
                                    {/* Video Icon and Title */}
                                    <div className="flex items-center space-x-4 mb-4">
                                      <div className="w-12 h-12 bg-white bg-opacity-20 rounded-lg flex items-center justify-center text-2xl">
                                        🌐
                                      </div>
                                      <div>
                                        <h6 className="font-bold text-lg">{content.title}</h6>
                                        <p className="text-blue-100 text-sm">External Video</p>
                                      </div>
                                    </div>
                                    
                                    {/* External Video Button */}
                                    <a 
                                      href={content.content_data} 
                                      target="_blank" 
                                      rel="noopener noreferrer" 
                                      className="block w-full bg-white text-blue-600 text-center py-4 px-6 rounded-lg font-bold text-lg hover:bg-blue-50 transition-colors duration-200 shadow-lg"
                                    >
                                      🎥 WATCH VIDEO
                                    </a>
                                    
                                    {/* Video URL Display */}
                                    <div className="mt-3 text-center">
                                      <p className="text-blue-100 text-sm">
                                        🔗 External video link
                                      </p>
                                      <p className="text-blue-200 text-xs mt-1 break-all">
                                        {content.content_data}
                                      </p>
                                    </div>
                                  </div>
                                );
                              }
                            })()}
                          </div>
                        ) : 
                        
                        /* Image Content */
                        content.content_type === 'image' ? (
                          <div className="mt-3">
                            <img
                              src={content.content_data}
                              alt={content.title}
                              className="w-full h-48 object-cover rounded-lg"
                              onError={(e) => {
                                e.target.style.display = 'none';
                                const fallbackDiv = e.target.parentElement.querySelector('.image-fallback');
                                if (fallbackDiv) {
                                  fallbackDiv.style.display = 'block';
                                }
                              }}
                            />
                            <div className="image-fallback hidden p-4 bg-gray-100 rounded-lg text-center">
                              <p className="text-gray-600">🖼️ Image: {content.content_data}</p>
                            </div>
                          </div>
                        ) : 
                        
                        /* Document Content */
                        content.content_type === 'document' ? (
                          <div className="mt-3">
                            <a
                              href={content.content_data}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="inline-flex items-center px-4 py-2 bg-blue-100 text-blue-800 rounded-lg hover:bg-blue-200 transition-colors"
                            >
                              📄 View Document
                            </a>
                            <p className="text-xs text-gray-500 mt-2">{content.content_data}</p>
                          </div>
                        ) : 
                        
                        /* Text Content */
                        (
                          <div className="mt-3">
                            <p className="text-gray-700 text-sm leading-relaxed whitespace-pre-wrap">
                              {content.content_data}
                            </p>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Assignments */}
              {chapterDetails.assignments && chapterDetails.assignments.length > 0 && (
                <div className="mb-6">
                  <h4 className="text-lg font-semibold text-gray-900 mb-4">📋 Assignments</h4>
                  <div className="space-y-4">
                    {chapterDetails.assignments.map((assignment) => (
                      <div key={assignment.id} className="border-l-4 border-orange-400 pl-4 py-3 bg-orange-50 rounded-r-lg">
                        <h5 className="font-medium text-orange-900 mb-1">{assignment.title}</h5>
                        <p className="text-orange-800 text-sm mb-2">{assignment.description}</p>
                        <div className="flex justify-between items-center text-sm text-orange-700">
                          <span>Points: {assignment.points}</span>
                          {assignment.due_date && (
                            <span>Due: {new Date(assignment.due_date).toLocaleDateString()}</span>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Quizzes */}
              {chapterDetails.quizzes && chapterDetails.quizzes.length > 0 && (
                <div className="mb-6">
                  <h4 className="text-lg font-semibold text-gray-900 mb-4">🎯 Quizzes</h4>
                  <div className="space-y-4">
                    {chapterDetails.quizzes.map((quiz) => (
                      <div key={quiz.id} className="border-l-4 border-purple-400 pl-4 py-3 bg-purple-50 rounded-r-lg">
                        <h5 className="font-medium text-purple-900 mb-1">{quiz.title}</h5>
                        <p className="text-purple-800 text-sm mb-2">{quiz.description}</p>
                        <div className="flex justify-between items-center text-sm text-purple-700">
                          <span>Questions: {quiz.questions.length}</span>
                          <span>Time Limit: {quiz.time_limit} minutes</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Upload Button */}
          {selectedChapter && (
            <div className="mt-8 bg-white rounded-lg shadow-md p-6 text-center">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">📤 Want to Add More Content?</h3>
              <p className="text-gray-600 mb-6">
                Upload additional educational materials to enrich this chapter for all students.
              </p>
              <button
                onClick={() => setShowUploadModal(true)}
                className="bg-indigo-600 hover:bg-indigo-700 text-white px-8 py-4 rounded-lg text-lg font-medium transition-all duration-200 shadow-lg hover:shadow-xl transform hover:scale-105"
              >
                📤 Upload Content
              </button>
            </div>
          )}

          {/* Upload Modal */}
          <UploadModal />
        </div>
      </div>
    );
  };

  // Main render logic
  if (!user) {
    return currentView === 'login' ? <LoginForm /> : <SignupForm />;
  }

  return <Dashboard />;
}

export default App;