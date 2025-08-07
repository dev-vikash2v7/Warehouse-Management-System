import axios from 'axios';

const axiosInstance = axios.create({
  baseURL: 'https://warehouse-management-backend.vercel.app',

});

export default axiosInstance;
