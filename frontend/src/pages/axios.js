import axios from 'axios';

const axiosInstance = axios.create({
  baseURL: 'https://reacttubevideos.firebaseapp.com',

});

export default axiosInstance;
