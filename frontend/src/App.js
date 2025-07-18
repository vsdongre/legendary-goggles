import React, { useState, useEffect } from 'react';
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
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [uploadData, setUploadData] = useState({
    title: '',
    content_type: 'text',
    content_data: ''
  });

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

  const handleUpload = async (e) => {
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
        // Refresh chapter details
        fetchChapterDetails(selectedChapter.id);
      } else {
        const errorData = await response.json();
        alert(errorData.detail || 'Upload failed');
      }
    } catch (err) {
      alert('Network error. Please try again.');
    }
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
              E-Learning Platform
            </h2>
            <p className="mt-2 text-center text-sm text-gray-600">
              Sign in to access your classes
            </p>
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

  const Dashboard = () => {
    return (
      <div className="min-h-screen bg-gray-50">
        <nav className="bg-white shadow-sm">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between h-16">
              <div className="flex items-center">
                <h1 className="text-xl font-semibold text-gray-900">E-Learning Platform</h1>
              </div>
              <div className="flex items-center space-x-4">
                <span className="text-gray-700">Welcome, {user.username}!</span>
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
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Select Class</h2>
              <div className="space-y-2">
                {classes.map((classData) => (
                  <button
                    key={classData.id}
                    onClick={() => handleClassSelect(classData)}
                    className={`w-full text-left p-3 rounded-md border ${
                      selectedClass?.id === classData.id
                        ? 'bg-indigo-100 border-indigo-500 text-indigo-900'
                        : 'bg-gray-50 border-gray-200 hover:bg-gray-100'
                    }`}
                  >
                    <div className="font-medium">{classData.name}</div>
                    <div className="text-sm text-gray-500">{classData.description}</div>
                  </button>
                ))}
              </div>
            </div>

            {/* Subject Selection */}
            <div className="bg-white rounded-lg shadow-md p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Select Subject</h2>
              {selectedClass ? (
                <div className="space-y-2">
                  {subjects.map((subject) => (
                    <button
                      key={subject.id}
                      onClick={() => handleSubjectSelect(subject)}
                      className={`w-full text-left p-3 rounded-md border ${
                        selectedSubject?.id === subject.id
                          ? 'bg-green-100 border-green-500 text-green-900'
                          : 'bg-gray-50 border-gray-200 hover:bg-gray-100'
                      }`}
                    >
                      <div className="font-medium">{subject.name}</div>
                      <div className="text-sm text-gray-500">{subject.description}</div>
                    </button>
                  ))}
                </div>
              ) : (
                <p className="text-gray-500 text-sm">Please select a class first</p>
              )}
            </div>

            {/* Chapter Selection */}
            <div className="bg-white rounded-lg shadow-md p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Select Chapter</h2>
              {selectedSubject ? (
                <div className="space-y-2">
                  {chapters.map((chapter) => (
                    <button
                      key={chapter.id}
                      onClick={() => handleChapterSelect(chapter)}
                      className={`w-full text-left p-3 rounded-md border ${
                        selectedChapter?.id === chapter.id
                          ? 'bg-blue-100 border-blue-500 text-blue-900'
                          : 'bg-gray-50 border-gray-200 hover:bg-gray-100'
                      }`}
                    >
                      <div className="font-medium">{chapter.name}</div>
                      <div className="text-sm text-gray-500">{chapter.description}</div>
                    </button>
                  ))}
                </div>
              ) : (
                <p className="text-gray-500 text-sm">Please select a subject first</p>
              )}
            </div>
          </div>

          {/* Chapter Details */}
          {chapterDetails && (
            <div className="mt-8 bg-white rounded-lg shadow-md p-6">
              <div className="mb-6">
                <h3 className="text-xl font-bold text-gray-900 mb-2">
                  {chapterDetails.chapter.name}
                </h3>
                <div className="text-sm text-gray-600 mb-4">
                  {chapterDetails.class.name} → {chapterDetails.subject.name} → {chapterDetails.chapter.name}
                </div>
                <p className="text-gray-700 mb-4">{chapterDetails.chapter.description}</p>
                <div className="prose max-w-none">
                  <p className="text-gray-800 leading-relaxed">
                    {chapterDetails.chapter.content}
                  </p>
                </div>
              </div>

              {/* Additional Content */}
              {chapterDetails.content && chapterDetails.content.length > 0 && (
                <div className="mt-6">
                  <h4 className="text-lg font-semibold text-gray-900 mb-4">Additional Content</h4>
                  <div className="space-y-4">
                    {chapterDetails.content.map((content) => (
                      <div key={content.id} className="border rounded-md p-4">
                        <h5 className="font-medium text-gray-900 mb-2">{content.title}</h5>
                        <span className="inline-block bg-gray-100 text-gray-800 px-2 py-1 rounded text-sm mb-2">
                          {content.content_type}
                        </span>
                        <p className="text-gray-700">{content.content_data}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Upload Section */}
          {selectedChapter && (
            <div className="mt-8 bg-white rounded-lg shadow-md p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Upload Content</h3>
              <form onSubmit={handleUpload} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Content Title
                  </label>
                  <input
                    type="text"
                    value={uploadData.title}
                    onChange={(e) => setUploadData({...uploadData, title: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                    placeholder="Enter content title"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Content Type
                  </label>
                  <select
                    value={uploadData.content_type}
                    onChange={(e) => setUploadData({...uploadData, content_type: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                  >
                    <option value="text">Text</option>
                    <option value="video">Video URL</option>
                    <option value="document">Document</option>
                    <option value="image">Image URL</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Content Data
                  </label>
                  <textarea
                    value={uploadData.content_data}
                    onChange={(e) => setUploadData({...uploadData, content_data: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                    rows={4}
                    placeholder="Enter content data (text, URL, etc.)"
                    required
                  />
                </div>

                <button
                  type="submit"
                  className="w-full bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-md text-sm font-medium"
                >
                  Upload Content
                </button>
              </form>
            </div>
          )}
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