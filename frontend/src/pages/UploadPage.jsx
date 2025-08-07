import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, FileText, CheckCircle, AlertCircle, Play } from 'lucide-react';
import axios from './axios';

export const UploadPage = () => {
  const [mappingFile, setMappingFile] = useState(null);
  const [salesFile, setSalesFile] = useState(null);
  const [processing, setProcessing] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);

  const onMappingDrop = useCallback((acceptedFiles) => {
    setMappingFile(acceptedFiles[0]);
    setError(null);
  }, []);

  const onSalesDrop = useCallback((acceptedFiles) => {
    setSalesFile(acceptedFiles[0]);
    setError(null);
  }, []);

  const { getRootProps: getMappingRootProps, getInputProps: getMappingInputProps, isDragActive: isMappingDragActive } = useDropzone({
    onDrop: onMappingDrop,
    accept: {
      'text/csv': ['.csv'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/vnd.ms-excel': ['.xls']
    },
    multiple: false
  });

  const { getRootProps: getSalesRootProps, getInputProps: getSalesInputProps, isDragActive: isSalesDragActive } = useDropzone({
    onDrop: onSalesDrop,
    accept: {
      'text/csv': ['.csv'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/vnd.ms-excel': ['.xls'],
      'application/json': ['.json']
    },
    multiple: false
  });

  const uploadFile = async (file, endpoint) => {
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post(`/api/upload/${endpoint}`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.error || 'Upload failed');
    }
  };

  const processMapping = async () => {
    if (!mappingFile || !salesFile) {
      setError('Please upload both mapping and sales files');
      return;
    }

    setProcessing(true);
    setError(null);

    try {
      // Upload mapping file
      await uploadFile(mappingFile, 'mapping');
      
      // Upload sales file
      await uploadFile(salesFile, 'sales');
      
      // Process mapping
      const response = await axios.post('/api/process');
      
      console.log('Response data:', response.data);
      console.log('Stats:', response.data.stats);

      if (response.data.stats) {
        setResults(response.data.stats);
      } else {
        throw new Error('Invalid response format from server');
      }
      
    } catch (error) {
      console.log('Error:', error);
      if (error.response) {
        // Server responded with error status
        setError(error.response.data.error || `Server error: ${error.response.status}`);
      } else if (error.request) {
        // Network error
        setError('Network error: Unable to connect to server. Please check if the backend is running.');
      } else {
        // Other error
        setError(error.message || 'An unexpected error occurred');
      }
    } finally {
      setProcessing(false);
    }
  };

  const exportResults = async (format = 'csv') => {
    try {
      const response = await axios.post('/api/export', { format }, {
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `processed_sales.${format}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      setError('Export failed');
    }
  };

  return (
    <div className="max-w-4xl mx-auto">
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Upload & Process Data</h1>
        <p className="text-gray-600">Upload your SKU mapping and sales data files to get started</p>
      </div>

      <div className="grid md:grid-cols-2 gap-8 mb-8">
        {/* Mapping File Upload */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold mb-4 flex items-center">
            <FileText className="h-5 w-5 mr-2 text-blue-600" />
            SKU Mapping File
          </h2>
          
          <div
            {...getMappingRootProps()}
            className={`border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors ${
              isMappingDragActive
                ? 'border-blue-400 bg-blue-50'
                : mappingFile
                ? 'border-green-400 bg-green-50'
                : 'border-gray-300 hover:border-gray-400'
            }`}
          >
            <input {...getMappingInputProps()} />
            
            {mappingFile ? (
              <div className="flex items-center justify-center space-x-2">
                <CheckCircle className="h-5 w-5 text-green-600" />
                <span className="text-green-700 font-medium">{mappingFile.name}</span>
              </div>
            ) : (
              <div>
                <Upload className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-600">
                  {isMappingDragActive
                    ? 'Drop the mapping file here'
                    : 'Drag & drop mapping file here, or click to select'}
                </p>
                <p className="text-sm text-gray-500 mt-2">CSV, XLSX files accepted</p>
              </div>
            )}
          </div>
        </div>

        {/* Sales File Upload */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold mb-4 flex items-center">
            <FileText className="h-5 w-5 mr-2 text-green-600" />
            Sales Data File
          </h2>
          
          <div
            {...getSalesRootProps()}
            className={`border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors ${
              isSalesDragActive
                ? 'border-blue-400 bg-blue-50'
                : salesFile
                ? 'border-green-400 bg-green-50'
                : 'border-gray-300 hover:border-gray-400'
            }`}
          >
            <input {...getSalesInputProps()} />
            
            {salesFile ? (
              <div className="flex items-center justify-center space-x-2">
                <CheckCircle className="h-5 w-5 text-green-600" />
                <span className="text-green-700 font-medium">{salesFile.name}</span>
              </div>
            ) : (
              <div>
                <Upload className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-600">
                  {isSalesDragActive
                    ? 'Drop the sales file here'
                    : 'Drag & drop sales file here, or click to select'}
                </p>
                <p className="text-sm text-gray-500 mt-2">CSV, XLSX, JSON files accepted</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Process Button */}
      <div className="text-center mb-8">
        <button
          onClick={processMapping}
          disabled={!mappingFile || !salesFile || processing}
          className={`inline-flex items-center px-6 py-3 rounded-lg font-medium transition-colors ${
            !mappingFile || !salesFile || processing
              ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
              : 'bg-blue-600 text-white hover:bg-blue-700'
          }`}
        >
          {processing ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
              Processing...
            </>
          ) : (
            <>
              <Play className="h-4 w-4 mr-2" />
              Process Mapping
            </>
          )}
        </button>
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
          <div className="flex items-center">
            <AlertCircle className="h-5 w-5 text-red-600 mr-2" />
            <span className="text-red-700">{error}</span>
          </div>
        </div>
      )}

      {results && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-xl font-semibold mb-4">Processing Results</h3>
          
          <div className="grid md:grid-cols-3 gap-6 mb-6">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">{results.total_records}</div>
              <div className="text-sm text-gray-600">Total Records</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">{results.mapped_records}</div>
              <div className="text-sm text-gray-600">Mapped Records</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-orange-600">{results.mapping_rate.toFixed(1)}%</div>
              <div className="text-sm text-gray-600">Mapping Rate</div>
            </div>
          </div>

          {results.unmapped_count > 0 && (
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6">
              <div className="flex items-center">
                <AlertCircle className="h-5 w-5 text-yellow-600 mr-2" />
                <span className="text-yellow-700">
                  {results.unmapped_count} SKUs could not be mapped. Consider updating your mapping file.
                </span>
              </div>
            </div>
          )}

          <div className="flex space-x-4">
            <button
              onClick={() => exportResults('csv')}
              className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors"
            >
              Export CSV
            </button>
            <button
              onClick={() => exportResults('excel')}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
            >
              Export Excel
            </button>
          </div>
        </div>
      )}
    </div>
  );
}; 


// {
//   "message": "Mapping processed successfully",
//   "preview": [
//     {
//       "Customer State": "Goa",
//       "MSKU": "CSTE_0199_MB_MHA8_Brown",
//       "Order Date": "2025-01-31",
//       "Packet Id": NaN,
//       "Product Name": "FUSKED Money Heist Music Box Hand Cranked Collectable Wooden Engraved Musical Box Bella ciao Theme Music Tune musicbox",
//       "Quantity": 1,
//       "Reason for Credit Entry": "DELIVERED",
//       "SKU": "MONEY HEIST A-8_BROWN",
//       "Size": "Free Size",
//       "Sub Order No": "116614722958250112_1",
//       "Supplier Discounted Price (Incl GST and Commision)": 169.0,
//       "Supplier Listed Price (Incl. GST + Commission)": 169.0
//     },
//     {
//       "Customer State": "Karnataka",
//       "MSKU": "CSTE_0045_MB_LavienRose_Brown",
//       "Order Date": "2025-01-31",
//       "Packet Id": NaN,
//       "Product Name": "la vieen rose brown music box Toys",
//       "Quantity": 1,
//       "Reason for Credit Entry": "DELIVERED",
//       "SKU": "69UfqNAh",
//       "Size": "Free Size",
//       "Sub Order No": "116620058427683329_1",
//       "Supplier Discounted Price (Incl GST and Commision)": 144.0,
//       "Supplier Listed Price (Incl. GST + Commission)": 144.0
//     },
//     {
//       "Customer State": "Rajasthan",
//       "MSKU": "CSTE_0148_SG_ButterFly_RedGreen",
//       "Order Date": "2025-01-31",
//       "Packet Id": NaN,
//       "Product Name": "Dragon Fly Sunglass cool Sunglass, Rimless Frameless Butterfly Sun glasses Unisex Vintage Eyewear(Pink)",
//       "Quantity": 1,
//       "Reason for Credit Entry": "DELIVERED",
//       "SKU": "SG_ButterFly_LightgreenPink",
//       "Size": "Free Size",
//       "Sub Order No": "116665551169940800_1",
//       "Supplier Discounted Price (Incl GST and Commision)": 299.0,
//       "Supplier Listed Price (Incl. GST + Commission)": 299.0
//     },
//     {
//       "Customer State": "Punjab",
//       "MSKU": "CSTE_0148_SG_ButterFly_RedGreen",
//       "Order Date": "2025-01-31",
//       "Packet Id": NaN,
//       "Product Name": "Dragon Fly Sunglass cool Sunglass, Rimless Frameless Butterfly Sun glasses Unisex Vintage Eyewear(Pink)",
//       "Quantity": 1,
//       "Reason for Credit Entry": "DELIVERED",
//       "SKU": "SG_ButterFly_LightgreenPink",
//       "Size": "Free Size",
//       "Sub Order No": "116693533129338178_1",
//       "Supplier Discounted Price (Incl GST and Commision)": 299.0,
//       "Supplier Listed Price (Incl. GST + Commission)": 299.0
//     },
//     {
//       "Customer State": "Chandigarh",
//       "MSKU": "CSTE_0060_MB_YouAreMySunshine_Brown",
//       "Order Date": "2025-01-31",
//       "Packet Id": NaN,
//       "Product Name": "You are My Sunshine Music Boxes Gift, Laser Engraved Sunshine Wooden Musical Box Gifts for Birthday/Valentine's Day/Christmas (Normal)",
//       "Quantity": 1,
//       "Reason for Credit Entry": "DELIVERED",
//       "SKU": "YOU ARE MY SUNSHINE SUN_BROWN",
//       "Size": "Free Size",
//       "Sub Order No": "116733106110886400_1",
//       "Supplier Discounted Price (Incl GST and Commision)": 209.0,
//       "Supplier Listed Price (Incl. GST + Commission)": 209.0
//     },
//     {
//       "Customer State": "Uttar Pradesh",
//       "MSKU": "CSTE_0017_MB_HP_Brown",
//       "Order Date": "2025-01-31",
//       "Packet Id": NaN,
//       "Product Name": "FUSKED Wooden Theme Harry Potter Hand Cranked Collectable Engraved Music Box Brown(1 Piece)",
//       "Quantity": 1,
//       "Reason for Credit Entry": "DELIVERED",
//       "SKU": "v1nepfRR",
//       "Size": "Free Size",
//       "Sub Order No": "116748622021067458_1",
//       "Supplier Discounted Price (Incl GST and Commision)": 249.0,
//       "Supplier Listed Price (Incl. GST + Commission)": 249.0
//     },
//     {
//       "Customer State": "Maharashtra",
//       "MSKU": "CSTE_0148_SG_ButterFly_RedGreen",
//       "Order Date": "2025-01-31",
//       "Packet Id": NaN,
//       "Product Name": "Dragon Fly Sunglass cool Sunglass, Rimless Frameless Butterfly Sun glasses Unisex Vintage Eyewear(Pink)",
//       "Quantity": 1,
//       "Reason for Credit Entry": "CANCELLED",
//       "SKU": "SG_ButterFly_LightgreenPink",
//       "Size": "Free Size",
//       "Sub Order No": "116761597631910018_1",
//       "Supplier Discounted Price (Incl GST and Commision)": 284.0,
//       "Supplier Listed Price (Incl. GST + Commission)": 284.0
//     },
//     {
//       "Customer State": "Tamil Nadu",
//       "MSKU": "CSTE_0015_MB_HBD_Black",
//       "Order Date": "2025-01-31",
//       "Packet Id": NaN,
//       "Product Name": "Wooden Uniq Carved Hand Crank Happy-Birthday-Black Theme Music Box",
//       "Quantity": 1,
//       "Reason for Credit Entry": "RTO_COMPLETE",
//       "SKU": "6CKGxkiA",
//       "Size": "Free Size",
//       "Sub Order No": "116782049662233920_1",
//       "Supplier Discounted Price (Incl GST and Commision)": 237.0,
//       "Supplier Listed Price (Incl. GST + Commission)": 237.0
//     },
//     {
//       "Customer State": "Kerala",
//       "MSKU": "CSTE_0017_MB_HP_Brown",
//       "Order Date": "2025-01-31",
//       "Packet Id": NaN,
//       "Product Name": "FUSKED Wooden Theme Harry Potter Hand Cranked Collectable Engraved Music Box Brown(1 Piece)",
//       "Quantity": 1,
//       "Reason for Credit Entry": "CANCELLED",
//       "SKU": "v1nepfRR",
//       "Size": "Free Size",
//       "Sub Order No": "116818414793813312_1",
//       "Supplier Discounted Price (Incl GST and Commision)": 249.0,
//       "Supplier Listed Price (Incl. GST + Commission)": 249.0
//     },
//     {
//       "Customer State": "Chhattisgarh",
//       "MSKU": "CSTE_0044_MB_LaVienRose_Black",
//       "Order Date": "2025-01-31",
//       "Packet Id": NaN,
//       "Product Name": "Fusked ooden Antique Carved Hand Crank Black La Vie En Rose Theme Music Box",
//       "Quantity": 1,
//       "Reason for Credit Entry": "DELIVERED",
//       "SKU": "La Vie En Rose MB-Black",
//       "Size": "Free Size",
//       "Sub Order No": "116837736253648192_1",
//       "Supplier Discounted Price (Incl GST and Commision)": 151.0,
//       "Supplier Listed Price (Incl. GST + Commission)": 151.0
//     }
//   ],
//   "stats": {
//     "mapped_records": 48,
//     "mapping_rate": 100.0,
//     "total_records": 48,
//     "unmapped_count": 0,
//     "unmapped_skus": []
//   }
// }
