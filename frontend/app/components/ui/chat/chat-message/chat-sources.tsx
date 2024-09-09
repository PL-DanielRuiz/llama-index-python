import { Dialog } from "@headlessui/react";
import { Check, Copy } from "lucide-react";
import { useMemo, useState } from "react";
import { Button } from "../../button";
import {
  HoverCard,
  HoverCardContent,
  HoverCardTrigger,
} from "../../hover-card";
import { useCopyToClipboard } from "../hooks/use-copy-to-clipboard";
import { SourceData } from "../index";
import PdfDialog from "../widgets/PdfDialog";

const SCORE_THRESHOLD = 0.3;

function SourceNumberButton({
  index,
  onClick,
}: {
  index: number;
  onClick: () => void;
}) {
  return (
    <div
      className="text-xs w-5 h-5 rounded-full bg-gray-100 mb-2 flex items-center justify-center hover:text-white hover:bg-primary hover:cursor-pointer"
      onClick={onClick}
    >
      {index + 1}
    </div>
  );
}

type NodeInfo = {
  id: string;
  url?: string;
  text?: string; // Agregar campo text
  metadata?: { [key: string]: any }; // Agregar metadatos
};

export function ChatSources({ data }: { data: SourceData }) {
  const [selectedNode, setSelectedNode] = useState<NodeInfo | null>(null);

  const sources: NodeInfo[] = useMemo(() => {
    const nodesByPath: { [path: string]: NodeInfo } = {};

    data.nodes
      .filter((node) => (node.score ?? 1) > SCORE_THRESHOLD)
      .sort((a, b) => (b.score ?? 1) - (a.score ?? 1))
      .forEach((node) => {
        const fileName = node.metadata?.file_name;
        const nodeInfo = {
          id: node.id,
          url: node.url ?? (fileName ? `/api/files/data/${fileName}` : null),
          text: node.text, // Agregar texto
          metadata: node.metadata, // Agregar metadatos
        };
        const key = nodeInfo.url ?? nodeInfo.id;
        if (!nodesByPath[key]) {
          nodesByPath[key] = nodeInfo;
        }
      });

    return Object.values(nodesByPath);
  }, [data.nodes]);

  if (sources.length === 0) return null;

  return (
    <div className="space-x-2 text-sm">
      <span className="font-semibold">Sources:</span>
      <div className="inline-flex gap-1 items-center">
        {sources.map((nodeInfo: NodeInfo, index: number) => {
          if (nodeInfo.url?.endsWith(".pdf")) {
            return (
              <PdfDialog
                key={nodeInfo.id}
                documentId={nodeInfo.id}
                url={nodeInfo.url!}
                text={nodeInfo.text || ''} // Pasar el texto
                metadata={nodeInfo.metadata || {}} // Pasar los metadatos
                trigger={<SourceNumberButton index={index} onClick={() => setSelectedNode(nodeInfo)} />}
              />
            );
          }
          return (
            <div key={nodeInfo.id}>
              <HoverCard>
                <HoverCardTrigger>
                  <SourceNumberButton index={index} onClick={() => setSelectedNode(nodeInfo)} />
                </HoverCardTrigger>
                <HoverCardContent className="w-[320px]">
                  <NodeInfo nodeInfo={nodeInfo} />
                </HoverCardContent>
              </HoverCard>
            </div>
          );
        })}
      </div>

      {selectedNode && !selectedNode.url?.endsWith(".pdf") && (
        <Dialog open={!!selectedNode} onClose={() => setSelectedNode(null)}>
          <div className="fixed inset-0 bg-black/30" aria-hidden="true" />
          <div className="fixed inset-0 flex items-center justify-center p-4">
            <div className="bg-white p-6 rounded shadow-lg max-w-3xl w-full max-h-[80vh] overflow-y-auto">
              <Dialog.Title className="text-lg font-semibold">Node Details</Dialog.Title>
              <div className="mt-2">
                <h2 className="text-md font-semibold">Metadata</h2>
                <pre className="whitespace-pre-wrap bg-gray-100 p-2 rounded mb-4">{JSON.stringify(selectedNode.metadata, null, 2)}</pre>
                <h2 className="text-md font-semibold">Text</h2>
                <pre className="whitespace-pre-wrap bg-gray-100 p-2 rounded">{selectedNode.text}</pre>
              </div>
              <Button onClick={() => setSelectedNode(null)} className="mt-4">
                Close
              </Button>
            </div>
          </div>
        </Dialog>
      )}
    </div>
  );
}

function NodeInfo({ nodeInfo }: { nodeInfo: NodeInfo }) {
  const { isCopied, copyToClipboard } = useCopyToClipboard({ timeout: 1000 });

  if (nodeInfo.url) {
    return (
      <div className="flex items-center my-2">
        <a className="hover:text-blue-900" href={nodeInfo.url} target="_blank">
          <span>{nodeInfo.url}</span>
        </a>
        <Button
          onClick={() => copyToClipboard(nodeInfo.url!)}
          size="icon"
          variant="ghost"
          className="h-12 w-12 shrink-0"
        >
          {isCopied ? (
            <Check className="h-4 w-4" />
          ) : (
            <Copy className="h-4 w-4" />
          )}
        </Button>
      </div>
    );
  }

  return (
    <p>
      Sorry, unknown node type. Please add a new renderer in the NodeInfo
      component.
    </p>
  );
}
