import { PDFViewer, PdfFocusProvider } from "@llamaindex/pdf-viewer";
import { Button } from "../../button";
import {
  Drawer,
  DrawerClose,
  DrawerContent,
  DrawerHeader,
  DrawerTitle,
  DrawerTrigger,
} from "../../drawer";

export interface PdfDialogProps {
  documentId: string;
  url: string;
  text: string; // Añadido para el texto
  metadata: { [key: string]: any }; // Añadido para los metadatos
  trigger: React.ReactNode;
}

export default function PdfDialog({
  documentId,
  url,
  text,
  metadata,
  trigger,
}: PdfDialogProps) {
  return (
    <Drawer direction="left">
      <DrawerTrigger>{trigger}</DrawerTrigger>
      <DrawerContent className="w-screen h-screen flex flex-row">
        {/* Panel izquierdo (Texto y Metadatos) */}
        <div className="w-1/3 p-4 bg-gray-50 overflow-y-auto">
          <DrawerHeader className="flex justify-between items-center">
            <div className="space-y-2">
              <DrawerTitle>PDF Details</DrawerTitle>
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
        {/* Panel derecho (PDF Viewer) */}
        <div className="w-2/3 p-4 bg-white">
          <PdfFocusProvider>
            <PDFViewer
              file={{
                id: documentId,
                url: url,
              }}
              className="w-full h-full"
            />
          </PdfFocusProvider>
        </div>
      </DrawerContent>
    </Drawer>
  );
}
