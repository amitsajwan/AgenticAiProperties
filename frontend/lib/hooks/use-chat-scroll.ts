import { useEffect, useRef } from "react";

export function useChatScroll(dep: any[]) {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => { ref.current?.scrollIntoView({ behavior: "smooth" }); }, [dep]);
  return ref;
}


