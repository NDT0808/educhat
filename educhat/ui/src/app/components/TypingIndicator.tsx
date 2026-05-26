import { motion } from "motion/react";

export default function TypingIndicator() {
    return (
        <div className="flex gap-1.5 p-2 items-center">
            {[0, 1, 2].map((i) => (
                <motion.div
                    key={i}
                    className="w-2 h-2 bg-indigo-400 rounded-full"
                    animate={{
                        y: [0, -6, 0],
                        opacity: [0.6, 1, 0.6]
                    }}
                    transition={{
                        duration: 0.8,
                        repeat: Infinity,
                        ease: "easeInOut",
                        delay: i * 0.2
                    }}
                />
            ))}
        </div>
    );
}
