/**
 * @file kmain.c
 * @brief BonsaiOS Interactive Kernel with Sheaf Solver
 *
 * This kernel runs standalone after ExitBootServices.
 * Demonstrates wreath-sheaf algebraic OS design.
 */

#include "sheaf.h"

// Tegra Orin UART base address (from NVIDIA L4T docs)
// UART A is at physical address 0x03100000
#define UART_BASE 0x03100000UL

// UART registers (16550-compatible)
#define UART_THR  (*(volatile unsigned char *)(UART_BASE + 0x00))  // Transmit Holding Register
#define UART_IER  (*(volatile unsigned char *)(UART_BASE + 0x04))  // Interrupt Enable Register
#define UART_FCR  (*(volatile unsigned char *)(UART_BASE + 0x08))  // FIFO Control Register
#define UART_LCR  (*(volatile unsigned char *)(UART_BASE + 0x0C))  // Line Control Register
#define UART_LSR  (*(volatile unsigned char *)(UART_BASE + 0x14))  // Line Status Register
#define UART_LSR_THRE (1 << 5)  // Transmitter Holding Register Empty

/**
 * Initialize UART (in case firmware didn't)
 */
static void uart_init(void) {
    // Disable all interrupts
    UART_IER = 0x00;

    // Enable FIFO, clear TX/RX
    UART_FCR = 0x07;

    // 8 bits, no parity, one stop bit
    UART_LCR = 0x03;

    // Note: We assume baud rate already set by firmware
}

/**
 * Write a character to UART
 */
static void uart_putc(char c) {
    // Wait until transmitter is ready
    while (!(UART_LSR & UART_LSR_THRE))
        ;

    // Send character
    UART_THR = c;
}

/**
 * Read a character from UART (blocking)
 */
static char uart_getc(void) {
    // Wait until data is available
    while (!(UART_LSR & 0x01))
        ;

    // Read character
    return UART_THR;
}

/**
 * Write a string to UART
 */
static void uart_puts(const char *s) {
    while (*s) {
        if (*s == '\n') {
            uart_putc('\r');  // Add carriage return
        }
        uart_putc(*s++);
    }
}

/**
 * Simple string compare
 */
static int str_cmp(const char *s1, const char *s2) {
    while (*s1 && (*s1 == *s2)) {
        s1++;
        s2++;
    }
    return *(unsigned char *)s1 - *(unsigned char *)s2;
}

/**
 * Simple string length
 */
static int str_len(const char *s) {
    int len = 0;
    while (*s++) len++;
    return len;
}

/**
 * Process a command
 */
static void process_command(const char *cmd) {
    if (str_cmp(cmd, "help") == 0) {
        uart_puts("BonsaiOS Commands:\n");
        uart_puts("  help   - Show this help\n");
        uart_puts("  echo   - Echo back input\n");
        uart_puts("  sheaf  - Run sheaf solver demo\n");
        uart_puts("  status - Show system status\n");
    }
    else if (str_cmp(cmd, "echo") == 0) {
        uart_puts("Echo: ");
        uart_puts(cmd);
        uart_puts("\n");
    }
    else if (str_cmp(cmd, "sheaf") == 0) {
        uart_puts("\n=== Sheaf Solver Demo: Register Allocation ===\n\n");

        SheafProblem problem;
        sheaf_demo_register_allocation(&problem);

        uart_puts("Problem: Allocate registers across 2 basic blocks\n");
        uart_puts("  Patch 1 (block_a): 3 variables (x,y,z)\n");
        uart_puts("  Patch 2 (block_b): 2 variables (y,w)\n");
        uart_puts("  Gluing: Variable 'y' shared between blocks\n\n");

        uart_puts("Running algebraic solver...\n");
        int result = sheaf_solve(&problem);

        if (result == 0) {
            uart_puts("  [OK] Solver converged\n");
            uart_puts("  Residual (obstruction): ");

            // Print residual as integer (simplified)
            int residual_int = (int)(problem.residual * 1000);
            if (residual_int == 0) {
                uart_puts("0.000");
            } else {
                // Simple integer print
                char buf[16];
                int idx = 0;
                int temp = residual_int;
                if (temp == 0) {
                    buf[idx++] = '0';
                } else {
                    while (temp > 0) {
                        buf[idx++] = '0' + (temp % 10);
                        temp /= 10;
                    }
                }
                // Reverse
                for (int i = idx - 1; i >= 0; i--) {
                    uart_putc(buf[i]);
                }
            }
            uart_puts("\n");

            if (problem.converged) {
                uart_puts("  [OK] Optimal allocation found!\n");
            } else {
                uart_puts("  [WARN] Non-optimal (constraints conflict)\n");
            }
        } else {
            uart_puts("  [ERR] Solver failed\n");
        }

        uart_puts("\nThis demonstrates wreath-sheaf algebraic OS design.\n");
        uart_puts("Future: GPU-accelerated scheduling & compilation.\n");
    }
    else if (str_cmp(cmd, "status") == 0) {
        uart_puts("System Status:\n");
        uart_puts("  Kernel: Running\n");
        uart_puts("  UART: Active\n");
        uart_puts("  Wreath-sheaf: Initialized\n");
    }
    else if (str_len(cmd) > 0) {
        uart_puts("Unknown command: '");
        uart_puts(cmd);
        uart_puts("'\n");
        uart_puts("Type 'help' for available commands.\n");
    }
}

/**
 * Kernel entry point
 */
void kmain(void) {
    char cmd_buffer[64];
    int cmd_idx = 0;

    // Initialize UART
    uart_init();

    // Print banner
    uart_puts("\n\n");
    uart_puts("       _\n");
    uart_puts("      /\\\n");
    uart_puts("     /**\\     BonsaiOS Kernel v0.2\n");
    uart_puts("    /****\\    Wreath-sheaf: algebraic OS\n");
    uart_puts("   /******\\\n");
    uart_puts("  /********\\\n");
    uart_puts("     ||\n");
    uart_puts("\n");
    uart_puts("  [OK] Kernel running\n");
    uart_puts("  [OK] UART initialized\n");
    uart_puts("  [OK] Console ready\n");
    uart_puts("\nType 'help' for commands.\n");

    // Command loop
    while (1) {
        uart_puts("\nbonsai> ");
        cmd_idx = 0;

        // Read line
        while (1) {
            char c = uart_getc();

            if (c == '\r' || c == '\n') {
                uart_puts("\n");
                cmd_buffer[cmd_idx] = '\0';
                break;
            }
            else if (c == 127 || c == 8) {  // Backspace
                if (cmd_idx > 0) {
                    cmd_idx--;
                    uart_puts("\b \b");  // Erase character
                }
            }
            else if (c >= 32 && c < 127 && cmd_idx < 63) {  // Printable
                cmd_buffer[cmd_idx++] = c;
                uart_putc(c);  // Echo
            }
        }

        // Process command
        process_command(cmd_buffer);
    }
}
