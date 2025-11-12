
OUTPUT_FORMAT("elf64-littleaarch64")
OUTPUT_ARCH(aarch64)
ENTRY(_start)

MEMORY
{
    ram (rwx) : ORIGIN = 0x80000, LENGTH = 128M
}

    /DISCARD/ : {
        *(.comment)
        *(.ARM.exidx)
        *(.eh_frame)
    }
}

PHDRS
{
    text_phdr PT_LOAD ;
    data_phdr PT_LOAD ;
}

SECTIONS
{
    .text :
    {
        . = 0x80000; /* Kernel base address, adjust as needed for Orin */
        KEEP(*(.text.boot))
        *(.text)
        *(.text.*)
    } > ram AT> ram :text_phdr

    .rodata :
    {
        . = ALIGN(4K);
        *(.rodata)
        *(.rodata.*)
    } > ram AT> ram :text_phdr

    .data :
    {
        . = ALIGN(4K);
        *(.data)
        *(.data.*)
    } > ram AT> ram :data_phdr

    .bss :
    {
        . = ALIGN(4K);
        __bss_start = .;
        *(.bss)
        *(.bss.*)
        __bss_end = .;
    } > ram AT> ram :data_phdr
