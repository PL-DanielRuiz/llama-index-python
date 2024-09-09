import { Button } from "../../button";
import {
  Drawer,
  DrawerClose,
  DrawerContent,
  DrawerHeader,
  DrawerTitle,
  DrawerTrigger,
} from "../../drawer";
import { useEffect, useState } from "react";

export interface TxtDialogProps {
  url: string;
  text: string; // Texto adicional que se mostrará
  metadata: { [key: string]: any }; // Metadatos
  trigger: React.ReactNode;
}

export default function TxtDialog({
  url,
  text,
  metadata,
  trigger,
}: TxtDialogProps) {
  const [fileContent, setFileContent] = useState<string | null>(null);

  // Fetching the content of the text file
  useEffect(() => {
    const fetchFileContent = async () => {
      try {
        const response = await fetch(url);
        const content = await response.text();
        setFileContent(content);
      } catch (error) {
        console.error("Error fetching file:", error);
        setFileContent("Error loading file content.");
      }
    };

    fetchFileContent();
  }, [url]);

  return (
    <Drawer direction="left">
      <DrawerTrigger>{trigger}</DrawerTrigger>
      <DrawerContent className="w-screen h-screen flex flex-row">
        {/* Panel izquierdo (Texto y Metadatos) */}
        <div className="w-1/3 p-4 bg-gray-50 overflow-y-auto">
          <DrawerHeader className="flex justify-between items-center">
            <div className="space-y-2">
              <DrawerTitle>File Details</DrawerTitle>
              <div>
                File URL:{" "}
                <a className="hover:text-blue-900" href={url} target="_blank">
                  {url}
                </a>
              </div>
            </div>
            <DrawerClose asChild>
              <Button variant="outline">Close</Button>
            </DrawerClose>
          </DrawerHeader>
          <div className="mt-4">
            <h2 className="text-md font-semibold">Metadata</h2>
            <pre className="whitespace-pre-wrap bg-gray-100 p-2 rounded mb-4">
              {JSON.stringify(metadata, null, 2)}
            </pre>
            <h2 className="text-md font-semibold">Text</h2>
            <pre className="whitespace-pre-wrap bg-gray-100 p-2 rounded">
              {text}
            </pre>
          </div>
        </div>
        {/* Panel derecho (Contenido del archivo) */}
        <div className="w-2/3 p-4 bg-white overflow-y-auto">
          <h2 className="text-md font-semibold mb-4">File Content</h2>
          {fileContent ? (
            <pre className="whitespace-pre-wrap bg-gray-50 p-4 rounded">
              {fileContent}
            </pre>
          ) : (
            <p>Loading file content...</p>
          )}
        </div>
      </DrawerContent>
    </Drawer>
  );
}
