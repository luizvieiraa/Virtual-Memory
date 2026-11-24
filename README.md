# Implementação 7 - Memória virtual

Autor: Luiz Henrique Carvalho Vieira. Identificador de entrega: `lhcv`.

Simulador em C11 com 256 páginas lógicas, páginas de 256 bytes, 128 frames
físicos e TLB de 16 entradas. As políticas FIFO e LRU são independentes para
páginas e TLB. A busca na TLB usa 16 threads POSIX por endereço, uma por entrada.
O enunciado traz "Implementação 6" no cabeçalho; esta é a atividade 7 - VM.

## Compilar e executar

Em Linux, Unix ou macOS, use um compilador C com POSIX threads e Make:

```sh
make
./vm addresses.txt lru fifo
make clean
```

Execute `make` na raiz deste repositório. O primeiro argumento é o arquivo de
endereços; o segundo escolhe a política de páginas e o terceiro a da TLB.
Cada política aceita exatamente `fifo` ou `lru`, em minúsculas.

Coloque `BACKING_STORE.bin` no diretório de execução. O arquivo original deve
conter as 256 páginas (65.536 bytes). Os anexos do professor não são versionados.
O arquivo de entrada contém um inteiro decimal de 0 a 65535 por linha; espaços
nas extremidades são aceitos. Arquivos vazios e linhas vazias são rejeitados.

O programa gera **`correct.txt` no diretório de execução**, sobrescrevendo a
saída anterior. Guarde o gabarito do professor com outro nome, por exemplo
`gabarito.txt`. A saída tem este formato:

```text
Virtual address: 16916 TLB: 0 Physical address: 20 Value: 0
```

O valor acima é o exemplo do gabarito e depende do binário original. `TLB` indica
o índice da entrada usada, inclusive quando a tradução acabou de ser inserida.
Ao final são escritos o total de endereços, page faults, taxa de page faults,
hits da TLB e taxa de hits, com três casas decimais nas taxas.

```sh
./vm addresses.txt lru fifo
diff -u gabarito.txt correct.txt
```

Uma execução bem-sucedida retorna 0. Erros retornam valor diferente de 0 e
mensagem em stderr: argumentos inválidos, arquivo ausente, entrada malformada,
página incompleta, falha na saída ou criação de threads. Uma saída parcial de
execução que falhou não deve ser usada como resultado válido.

## Organização e algoritmos

`vm.c` concentra a leitura, tradução, substituição e busca paralela. O endereço
é decomposto em `página = endereço / 256` e `deslocamento = endereço % 256`.
Os frames livres são preenchidos em ordem de 0 a 127. Em page fault, a página
é lida na posição `página * 256` do backing store. A tradução física é
`frame * 256 + deslocamento`; o byte é convertido para o intervalo -128 a 127.

FIFO de páginas mantém um índice circular de vítima, atualizado apenas nas
substituições. LRU mantém posições de recência limitadas a 0..127 e atualiza
a ordem em todo acesso, incluindo hits da TLB. Ao remover uma página, seu
mapeamento na tabela e qualquer entrada correspondente na TLB são invalidados.

A TLB preenche a primeira entrada livre. Quando cheia, remove a de menor
marcador: inserção para FIFO, último acesso para LRU. As threads recebem cópias
das entradas e resultados separados; a principal aguarda todas com
`pthread_join` antes de atualizar qualquer estrutura. A busca paralela é uma
simulação didática: criar 16 threads por acesso pode custar mais que uma busca
sequencial de 16 entradas; não é alegada melhoria de desempenho.

## Testes e evidências

As verificações registradas no log usaram dados sintéticos e um modelo
independente para conferir as quatro combinações de políticas, além de casos
de erro. As ferramentas auxiliares usadas nessa validação não integram a entrega.
Para reproduzir a comparação com o professor, execute `./vm addresses.txt lru fifo`
e `diff -u gabarito.txt correct.txt` com os anexos na pasta.

Consulte `evidencias.log` para os resultados efetivamente obtidos. A referência
`lru fifo` tem 1000 traduções, 539 page faults (0.539) e 54 hits (0.054).
Em 24/11/2026, a comparação completa passou com o
[binário oficial do livro](https://github.com/greggagne/OSC10e/blob/master/ch10/BACKING_STORE.bin):
as 1.005 linhas de `correct.txt` coincidiram byte a byte com o gabarito,
incluindo os valores. `cmp` não encontrou diferenças e os SHA-256 são iguais.

No Windows com MinGW-w64 e winpthreads, a compilação também foi testada:

```powershell
mingw32-make -B CC=gcc
mingw32-make clean RM="cmd /c del /Q"
```

Linux foi validado no Ubuntu via WSL. Unix e macOS não foram executados.
Ao alternar entre Windows e WSL no mesmo diretório, limpe ou force a
recompilação: os executáveis de cada sistema têm formatos diferentes.

## Entrega

```sh
tar -tf lhcv.tar
```

O pacote contém somente `lhcv/vm.c` e `lhcv/Makefile`, conforme o enunciado.
Após extrair, entre em `lhcv/` e execute `make`. A compilação depende somente
do compilador C, de POSIX threads e do Make.

- GitHub: `vm.c`, `Makefile`, este README, `evidencias.log` e `lhcv.pdf`. Os commits anteriores preservam as versões por etapa.
- Classroom: enviar **`lhcv.pdf` e `lhcv.tar` separadamente**.
- Não incluir executáveis, anexos do professor ou `correct.txt` no `.tar`.

Não foi realizado envio ao Classroom nem push automático.
