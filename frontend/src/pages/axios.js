import axios from 'axios';

const axiosInstance = axios.create({
  baseURL: 'https://warehouse-management-system-isjh.onrender.com',
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: false, // change to true if using cookies/session
});

export default axiosInstance;
