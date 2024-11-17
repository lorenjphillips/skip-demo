'use client';

import { useEffect, useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';

const ApiDebug = () => {
  const [apiStatus, setApiStatus] = useState<{
    url?: string;
    health?: string;
    error?: string;
  }>({});

  useEffect(() => {
    const checkApi = async () => {
      const url = process.env.NEXT_PUBLIC_API_URL;
      setApiStatus(prev => ({ ...prev, url }));
      
      try {
        const response = await fetch(`${url}/health`);
        const data = await response.json();
        setApiStatus(prev => ({ 
          ...prev, 
          health: JSON.stringify(data, null, 2) 
        }));
      } catch (error) {
        setApiStatus(prev => ({ 
          ...prev, 
          error: error instanceof Error ? error.message : 'Unknown error' 
        }));
      }
    };

    checkApi();
  }, []);

  if (!apiStatus.url) return null;

  return (
    <Card className="fixed bottom-4 right-4 w-96 bg-white/90 backdrop-blur-sm">
      <CardHeader>
        <CardTitle>API Debug Info</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-2 text-sm">
          <div>
            <strong>API URL:</strong>
            <pre className="mt-1 p-2 bg-gray-100 rounded">{apiStatus.url}</pre>
          </div>
          {apiStatus.health && (
            <div>
              <strong>Health Check:</strong>
              <pre className="mt-1 p-2 bg-gray-100 rounded">{apiStatus.health}</pre>
            </div>
          )}
          {apiStatus.error && (
            <div>
              <strong>Error:</strong>
              <pre className="mt-1 p-2 bg-red-100 rounded">{apiStatus.error}</pre>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

export default ApiDebug;