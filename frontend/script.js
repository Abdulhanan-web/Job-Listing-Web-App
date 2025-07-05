document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('job-form');
  const jobList = document.getElementById('job-list');
  const searchInput = document.getElementById('search-input');
  const sortSelect = document.getElementById('sort-select');
  const filterType = document.getElementById('filter-type');
  let jobs = [];
  let editingJobId = null;

  // Initialize the app
  fetchJobs();

  // Form submission handler
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const jobData = {
      title: document.getElementById('title').value.trim(),
      company: document.getElementById('company').value.trim(),
      location: document.getElementById('location').value.trim(),
      job_type: document.getElementById('job_type').value,
      tags: document.getElementById('tags').value
        ? document.getElementById('tags').value.split(',').map(tag => tag.trim())
        : []
    };

    try {
      if (editingJobId) {
        await updateJob(editingJobId, jobData);
        editingJobId = null;
        form.querySelector('button').textContent = 'Add Job';
      } else {
        await createJob(jobData);
      }
      form.reset();
      await fetchJobs();
    } catch (error) {
      console.error('Error saving job:', error);
      alert('Failed to save job. Please check console for details.');
    }
  });

  // Event listeners for search/filter
  searchInput.addEventListener('input', renderJobs);
  sortSelect.addEventListener('change', renderJobs);
  filterType.addEventListener('change', renderJobs);

  // Fetch jobs from API
  async function fetchJobs() {
    try {
      const response = await fetch('/jobs');
      if (!response.ok) throw new Error('Failed to fetch jobs');
      jobs = await response.json();
      renderJobs();
    } catch (error) {
      console.error('Error fetching jobs:', error);
    }
  }

  // Render jobs to the DOM
  function renderJobs() {
    jobList.innerHTML = '';

    let filteredJobs = filterJobs();
    sortJobs(filteredJobs);

    if (filteredJobs.length === 0) {
      jobList.innerHTML = '<li class="no-jobs">No jobs found matching your criteria</li>';
      return;
    }

    filteredJobs.forEach(job => {
      const jobItem = document.createElement('li');
      jobItem.className = 'job-item';
      
      jobItem.innerHTML = `
        <div class="job-header">
          <h3>${job.title}</h3>
          <span class="company">${job.company}</span>
        </div>
        <div class="job-details">
          <span class="location">📍 ${job.location}</span>
          <span class="job-type">${job.job_type}</span>
          <span class="date-posted">📅 ${formatDate(job.posting_date)}</span>
        </div>
        ${job.tags?.length ? `<div class="job-tags">${job.tags.map(tag => `<span class="tag">${tag}</span>`).join('')}</div>` : ''}
        <div class="job-actions"></div>
      `;

      const actionsDiv = jobItem.querySelector('.job-actions');
      
      // Edit button
      const editBtn = document.createElement('button');
      editBtn.className = 'edit-button';
      editBtn.innerHTML = '<i class="fas fa-edit"></i> Edit';
      editBtn.onclick = () => loadJobIntoForm(job);
      console.log('Appending edit button for:', job.title);
      actionsDiv.appendChild(editBtn);

      // Delete button
      const deleteBtn = document.createElement('button');
      deleteBtn.className = 'delete-btn';
      deleteBtn.innerHTML = '<i class="fas fa-trash"></i> Delete';
      deleteBtn.onclick = () => confirmDelete(job.id);
      actionsDiv.appendChild(deleteBtn);

      jobList.appendChild(jobItem);
    });
  }

  // Filter jobs based on search and type
  function filterJobs() {
    let filtered = [...jobs];
    const searchTerm = searchInput.value.toLowerCase();
    const selectedType = filterType.value;

    if (searchTerm) {
      filtered = filtered.filter(job => 
        job.title.toLowerCase().includes(searchTerm) || 
        job.company.toLowerCase().includes(searchTerm)
      );
    }

    if (selectedType) {
      filtered = filtered.filter(job => job.job_type === selectedType);
    }

    return filtered;
  }

  // Sort jobs by date
  function sortJobs(jobsArray) {
    const sortBy = sortSelect.value;
    jobsArray.sort((a, b) => {
      const dateA = new Date(a.posting_date);
      const dateB = new Date(b.posting_date);
      return sortBy === 'newest' ? dateB - dateA : dateA - dateB;
    });
  }

  // Format date as "X days ago"
  function formatDate(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diffDays = Math.floor((now - date) / (1000 * 60 * 60 * 24));
    
    if (diffDays === 0) return 'Today';
    if (diffDays === 1) return 'Yesterday';
    if (diffDays < 7) return `${diffDays} days ago`;
    
    return date.toLocaleDateString();
  }

  // Create new job
  async function createJob(jobData) {
    const response = await fetch('/jobs', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(jobData)
    });
    
    if (!response.ok) throw new Error('Failed to create job');
    return await response.json();
  }

  // Update existing job
  async function updateJob(id, jobData) {
    const response = await fetch(`/jobs/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(jobData)
    });
    
    if (!response.ok) throw new Error('Failed to update job');
    return await response.json();
  }

  // Confirm before deleting
  async function confirmDelete(id) {
    if (confirm('Are you sure you want to delete this job?')) {
      try {
        const response = await fetch(`/jobs/${id}`, { method: 'DELETE' });
        if (!response.ok) throw new Error('Failed to delete job');
        await fetchJobs();
      } catch (error) {
        console.error('Error deleting job:', error);
        alert('Failed to delete job');
      }
    }
  }

  // Load job into form for editing
  function loadJobIntoForm(job) {
    document.getElementById('title').value = job.title;
    document.getElementById('company').value = job.company;
    document.getElementById('location').value = job.location;
    document.getElementById('job_type').value = job.job_type;
    document.getElementById('tags').value = job.tags?.join(', ') || '';
    editingJobId = job.id;
    form.querySelector('button').textContent = 'Update Job';
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }
});