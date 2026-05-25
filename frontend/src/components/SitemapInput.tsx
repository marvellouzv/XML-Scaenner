import { LoaderCircle } from "lucide-react";
import { FormEvent, useMemo, useState } from "react";
import { useLoadSitemapMutation } from "../hooks/useSitemapQuery";
import { Button } from "./ui/button";
import { Input } from "./ui/input";

function isValidSitemapUrl(url: string): boolean {
  try {
    const parsed = new URL(url);
    const protocolOk = parsed.protocol === "http:" || parsed.protocol === "https:";
    const path = parsed.pathname.toLowerCase();
    return protocolOk && (path.endsWith(".xml") || path.endsWith(".xml.gz") || path.includes("sitemap"));
  } catch {
    return false;
  }
}

export function SitemapInput() {
  const [url, setUrl] = useState("");
  const mutation = useLoadSitemapMutation();

  const errorText = useMemo(() => {
    if (!url) {
      return "";
    }
    return isValidSitemapUrl(url) ? "" : "URL должен быть http/https и вести на sitemap.xml или sitemap.xml.gz";
  }, [url]);

  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!isValidSitemapUrl(url)) {
      return;
    }
    mutation.mutate(url);
  };

  const mutationErrorText = mutation.error instanceof Error ? mutation.error.message : "";

  return (
    <form onSubmit={submit} className="space-y-2">
      <div className="flex items-center gap-3">
        <Input
          value={url}
          onChange={(event) => setUrl(event.target.value)}
          placeholder="https://example.com/sitemap.xml"
          aria-label="Sitemap URL"
        />
        <Button type="submit" disabled={mutation.isPending || Boolean(errorText)}>
          {mutation.isPending ? <LoaderCircle className="h-4 w-4 animate-spin" /> : "LOAD"}
        </Button>
      </div>
      {errorText ? <p className="text-xs text-red-400">{errorText}</p> : null}
      {mutationErrorText ? <p className="text-xs text-red-400">{mutationErrorText}</p> : null}
    </form>
  );
}
