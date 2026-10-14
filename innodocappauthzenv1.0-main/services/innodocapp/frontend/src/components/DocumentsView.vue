<template>
  <div class="documents-container">
    <!-- Header -->
    <div class="documents-header">
      <h1>Documents</h1>
      <button @click="logout" class="btn btn-logout">Logout</button>
    </div>

    <!-- Search Bar -->
    <div class="search-section">
      <div class="search-controls">
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Enter document path to search..."
          class="search-input"
          @keyup.enter="searchDocument"
        />
        <button @click="searchDocument" class="btn btn-search">Search</button>
        <button @click="resetSearch" class="btn btn-secondary">Clear</button>
      </div>
    </div>

    <!-- Error Alert -->
    <div v-if="errorMessage" class="alert alert-error">
      {{ errorMessage }}
      <button @click="errorMessage = ''" class="close-btn">×</button>
    </div>

    <!-- Loading State -->
    <div v-if="isLoading" class="loading">
      <p>Loading documents...</p>
    </div>

    <!-- Search Results -->
    <div
      v-else-if="searchActive && searchedDocuments.length"
      class="documents-section"
    >
      <h2>Search Result</h2>
      <div class="documents-list">
        <div
          v-for="doc in searchedDocuments"
          :key="doc.file_id"
          class="document-card"
        >
          <h3>{{ doc.file_path }}</h3>
          <p><strong>ID:</strong> {{ doc.file_id }}</p>
          <p class="content-preview">
            <strong>Content:</strong> {{ doc.content }}
          </p>
          <button @click="viewDocument(doc)" class="btn btn-primary">
            View Document
          </button>
        </div>
      </div>
    </div>

    <!-- All Documents List -->
    <div v-else-if="!searchActive" class="documents-section">
      <h2>All Documents</h2>
      <div v-if="documents.length === 0" class="no-documents">
        <p>No documents available.</p>
      </div>
      <div v-else class="documents-list">
        <div v-for="doc in documents" :key="doc.file_id" class="document-card">
          <h3>{{ doc.file_path }}</h3>
          <p><strong>ID:</strong> {{ doc.file_id }}</p>
          <p class="content-preview">
            <strong>Content:</strong> {{ doc.content }}
          </p>
          <button @click="viewDocument(doc)" class="btn btn-primary">
            View Document
          </button>
        </div>
      </div>
    </div>

    <!-- No Search Results -->
    <div
      v-else-if="searchActive && searchedDocuments.length === 0 && !isLoading"
      class="no-results"
    >
      <p>
        No document found with ID: <strong>{{ searchQuery }}</strong>
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import endpoints from "@/api/endpoints";

const documents = ref([]);
const searchQuery = ref("");
const searchedDocuments = ref([]);
const searchActive = ref(false);
const isLoading = ref(false);
const errorMessage = ref("");

const oidc_config = process.env.VUE_APP_OIDC_CONFIG;
const oidc_redirect = process.env.VUE_APP_OIDC_REDIRECT;
const oidc_config_dict = ref(null);

// Code Verifier for PKCE
function generateCodeVerifier() {
  const array = new Uint8Array(32);
  window.crypto.getRandomValues(array);

  let base64String = btoa(String.fromCharCode(...array));

  const base64Url = base64String
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=+$/, '');

  return base64Url;
}

async function generateCodeChallenge(codeVerifier) {
  const encoder = new TextEncoder();
  const data = encoder.encode(codeVerifier);

  const digest = await crypto.subtle.digest('SHA-256', data);
  const hashArray = new Uint8Array(digest);
  let base64String = btoa(String.fromCharCode(...hashArray));

  return base64String
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=+$/, '');
}

async function loadOidcConfig() {
  const response = await fetch(oidc_config);
  oidc_config_dict.value = await response.json();
}

async function getOidcValue(key) {
  if (!oidc_config_dict.value) {
    await loadOidcConfig();
  }
  return oidc_config_dict.value[key];
}



// Fetch all documents on mount
onMounted(async () => {
  const params = new URLSearchParams(window.location.search);
  const code = params.get("code");
  if (code) {
    try {
      const formData = new URLSearchParams();
      formData.append('grant_type', 'authorization_code');
      formData.append('client_id', 'innodocapp');
      formData.append('code', code);
      formData.append('redirect_uri', oidc_redirect);
      const codeVerifier = localStorage.getItem("code_verifier");
      formData.append('code_verifier', codeVerifier);

      const oidc_token = await getOidcValue("token_endpoint");
      const response = await fetch(oidc_token, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        },
        body: formData
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      const jwtToken = data.access_token; // Extract Access Token
      const idToken = data.id_token; // Extract Id Token
      localStorage.setItem("jwt_token", jwtToken);
      localStorage.setItem("id_token", idToken);

    } catch (error) {
      console.error('Error fetching access token:', error);
      return;
    }

    // Clean up URL without the token
    window.history.replaceState({}, document.title, window.location.pathname);
  }
  if (localStorage.getItem("jwt_token") !== null) {
    fetchAllDocuments();
  } else {
    await handleUnauthorized();
  }
});

const handleUnauthorized = async () => {

  const codeVerifier = generateCodeVerifier();
  localStorage.setItem("code_verifier", codeVerifier);
  const codeChallenge = await generateCodeChallenge(codeVerifier);

  const oidc_auth = await getOidcValue("authorization_endpoint");
  const url = new URL(oidc_auth);

  url.searchParams.set('client_id', 'innodocapp');
  url.searchParams.set('response_type', 'code');
  url.searchParams.set('redirect_uri', oidc_redirect);
  url.searchParams.set('code_challenge', codeChallenge);
  url.searchParams.set('code_challenge_method', 'S256');
  url.searchParams.set('scope', 'openid');

  window.location.href = url.toString();
};


// Fetch all documents
const fetchAllDocuments = async () => {
  isLoading.value = true;
  errorMessage.value = "";
  try {
    const endpoint = endpoints.documents.getAll;
    const token = localStorage.getItem("jwt_token");
    const options = {
      method: endpoint.method //,
      // credentials: "include",
    };

    if (token) {
      options.headers = {
        Authorization: `Bearer ${token}`,
      };
    }

    const response = await fetch(endpoint.url, options);

    if (!response.ok) {
      if (response.status === 401) {
        await handleUnauthorized();
      }
      throw new Error(`Failed to fetch documents: ${response.statusText}`);
    }

    documents.value = await response.json();
  } catch (error) {
    console.error('Fetch-Fehler:', error);
    errorMessage.value = `Failed to load documents: ${error.message}`;
  } finally {
    isLoading.value = false;
  }
};

// Search for a specific document
const searchDocument = async () => {
  if (!searchQuery.value.trim()) {
    errorMessage.value = "Please enter a document path";
    return;
  }

  isLoading.value = true;
  errorMessage.value = "";
  searchActive.value = true;

  try {
    const endpoint = endpoints.documents.getById;
    const token = localStorage.getItem("jwt_token");
    const options = {
      method: endpoint.method //,
      // credentials: "include",
    };

    if (token) {
      options.headers = {
        Authorization: `Bearer ${token}`,
      };
    }

    const response = await fetch(endpoint.url(searchQuery.value), options);

    if (!response.ok) {
      if (response.status === 401) {
        handleUnauthorized()
      }
      throw new Error(response.statusText);
    }
    const result = await response.json();
    searchedDocuments.value = Array.isArray(result) ? result : [result];
  } catch (error) {
    searchedDocuments.value = [];
    errorMessage.value = error.message;
  } finally {
    isLoading.value = false;
  }
};

// Reset search and show all documents
const resetSearch = () => {
  searchQuery.value = "";
  searchedDocuments.value = [];
  searchActive.value = false;
  errorMessage.value = "";
};

const logout = async () => {
  const idToken = localStorage.getItem("id_token");
  localStorage.removeItem("jwt_token");
  localStorage.removeItem("id_token");
  documents.value = [];
  resetSearch();

  const oidc_logout = await getOidcValue("end_session_endpoint");
  const url = new URL(oidc_logout);
  url.searchParams.set('id_token_hint', idToken);
  url.searchParams.set('post_logout_redirect_uri', oidc_redirect);

  window.location.href = url.toString();
};

// View document (placeholder - implement as needed)
const viewDocument = (doc) => {
  // TODO: Implement document detail view or download
  alert(`Document: ${doc.file_path}\nID: ${doc.file_id}\n\n${doc.content}`);
};
</script>

<style scoped>
.documents-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

.documents-header {
  margin-bottom: 40px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.documents-header h1 {
  color: #2c3e50;
  font-size: 2.5rem;
  margin: 0;
}

.btn-logout {
  background: #e74c3c;
  color: #fff;
}

.btn-logout:hover {
  background: #c0392b;
}

/* Alerts */
.alert {
  padding: 15px 20px;
  margin-bottom: 20px;
  border-radius: 6px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.alert-warning {
  background-color: #fff3cd;
  color: #856404;
  border: 1px solid #ffeeba;
}

.alert-error {
  background-color: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
  position: relative;
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: inherit;
  padding: 0;
  margin-left: 10px;
}

.close-btn:hover {
  opacity: 0.7;
}

/* Search Section */
.search-section {
  margin-bottom: 40px;
}

.search-controls {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.search-input {
  flex: 1;
  min-width: 250px;
  padding: 12px 15px;
  font-size: 1rem;
  border: 1px solid #ddd;
  border-radius: 6px;
  transition: border-color 0.3s;
}

.search-input:focus {
  outline: none;
  border-color: #42b983;
  box-shadow: 0 0 5px rgba(66, 185, 131, 0.3);
}

/* Buttons */
.btn {
  padding: 12px 24px;
  font-size: 1rem;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.3s;
  font-weight: 500;
}

.btn-primary {
  background-color: #42b983;
  color: white;
}

.btn-primary:hover {
  background-color: #369970;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(66, 185, 131, 0.3);
}

.btn-secondary {
  background-color: #999;
  color: white;
}

.btn-secondary:hover {
  background-color: #777;
}

.btn-search {
  background-color: #2c5aa0;
  color: white;
}

.btn-search:hover {
  background-color: #1e3f5a;
}

/* Documents Section */
.documents-section {
  margin-top: 30px;
}

.documents-section h2 {
  color: #2c3e50;
  margin-bottom: 20px;
  font-size: 1.5rem;
}

.documents-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}

.document-card {
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 20px;
  transition: all 0.3s;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.document-card:hover {
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.15);
  transform: translateY(-4px);
}

.document-card h3 {
  color: #2c3e50;
  margin: 0 0 15px 0;
  font-size: 1.2rem;
  word-break: break-word;
}

.document-card p {
  margin: 10px 0;
  color: #555;
  font-size: 0.95rem;
}

.content-preview {
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: normal;
}

.document-card strong {
  color: #2c3e50;
}

.document-card .btn-primary {
  margin-top: 15px;
  width: 100%;
  text-align: center;
}

/* Loading State */
.loading {
  text-align: center;
  padding: 40px;
  color: #999;
  font-size: 1.1rem;
}

/* No Results */
.no-documents,
.no-results {
  text-align: center;
  padding: 40px;
  background-color: #f5f5f5;
  border-radius: 8px;
  color: #999;
  font-size: 1.1rem;
}
</style>
