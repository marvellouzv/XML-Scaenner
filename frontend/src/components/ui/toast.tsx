import { AnimatePresence, motion } from "framer-motion";

export function Toast({ message, show }: { message: string; show: boolean }) {
  return (
    <AnimatePresence>
      {show ? (
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: 20 }}
          className="fixed bottom-6 right-6 z-50 rounded-md border border-border bg-card px-4 py-2 text-sm text-foreground shadow-lg"
        >
          {message}
        </motion.div>
      ) : null}
    </AnimatePresence>
  );
}

