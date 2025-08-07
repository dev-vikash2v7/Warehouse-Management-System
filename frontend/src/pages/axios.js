import axios from 'axios';

const axiosInstance = axios.create({
  baseURL: 'https://warehouse-management-system-isjh.onrender.com'
});

export default axiosInstance;
