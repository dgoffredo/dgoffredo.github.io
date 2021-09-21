Tree Search
===========
How many ways can we search through a tree?  Let us count the ways.

Front Matter
------------
```c++
#include <vector>

template <typename Value>
struct Tree {
    Value value;
    std::vector<Tree> children;
};
```

Depth-first
-----------
Visit all of a node's descendants before visiting any of its siblings.
```c++
template <typename Value>
const Tree<Value>* depth_first_search(const Tree<Value>& tree, const Value& value) {
    if (tree.value == value) {
        return &tree;
    }

    for (const auto& child : tree.children) {
        if (const auto result = depth_first_search(child, value)) {
            return result;
        }
    }

    return nullptr;
}
```

Breadth-first
-------------
Visit all of a node's siblings before visiting any of its descendants.
```c++
#include <queue>

template <typename Value>
const Tree<Value>* breadth_first_search(const Tree<Value>& tree, const Value& value) {
    std::queue<const Tree<Value>*> to_visit;
    to_visit.push(&tree);
    
    for (;;) {
        const auto current = to_visit.front();
        to_visit.pop();
        if (current->value == value) {
            return current;
        }

        for (const auto& child : current->children) {
            to_visit.push(&child);
        }

        if (to_visit.empty()) {
            return nullptr;
        }
    }
}
```
This required a queue, and did not require recursion.

We could rewrite the depth-first search without recursion.  After all, the
call stack is a... stack.
```c++
#include <stack>
#include <vector>

template <typename Value>
const Tree<Value>* depth_first_search(const Tree<Value>& tree, const Value& value) {
    using Ptr = const Tree<Value>*;
    std::stack<Ptr, std::vector<Ptr>> to_visit;
    to_visit.push(&tree);
    
    for (;;) {
        const auto current = to_visit.top();
        to_visit.pop();
        if (current->value == value) {
            return current;
        }

        for (const auto& child : current->children) {
            to_visit.push(&child);
        }

        if (to_visit.empty()) {
            return nullptr;
        }
    }
}
```
This visits a node's children in the opposite order as before, but it's still a
depth-first search.

This also is technically less efficient than the first depth-first search, because
we copy a node's children into `to_visit` before visiting them.

The benefit of this second version is that it can accommodate trees that are
as deep as memory will allow, whereas the first version can only go as deep as
the call stack, which is usually much smaller.  Also, a call stack frame is
larger than a pointer, so we use less space by storing only the `Tree*` instead
of an entire stack frame.

Generalize
----------
The breadth-first search algorithm and the second depth-first search algorithm
are very similar.  The only difference is in the definition of `to_visit`.

Let's rewrite them as adaptations of the same underlying algorithm.
```c++
#include <queue>
#include <stack>
#include <vector>

template <typename Value, typename Container>
const Tree<Value>* search(const Tree<Value>& tree, const Value& value, Container&& to_visit) {
    to_visit.push(&tree);

    for (;;) {
        const auto current = to_visit.next();
        if (current->value == value) {
            return current;
        }

        for (const auto& child : current->children) {
            to_visit.push(&child);
        }

        if (to_visit.empty()) {
            return nullptr;
        }
    }
}

template <typename Value>
struct Stack : public std::stack<const Tree<Value>*, std::vector<const Tree<Value>*>> {
    const Tree<Value>*& next() const {
        return this->top();
    }
};

template <typename Value>
const Tree<Value>* depth_first_search(const Tree<Value>& tree, const Value& value) {
    return search(tree, value, Stack<Value>());
}

template <typename Value>
struct Queue : public std::queue<const Tree<Value>*> {
    const Tree<Value>*& next() const {
        return this->front();
    }
};

template <typename Value>
const Tree<Value>* breadth_first_search(const Tree<Value>& tree, const Value& value) {
    return search(tree, value, Queue<Value>());
}
```

What Else?
----------
What other data structures could we use for `to_visit`, other than a stack or a
queue?

If we don't know anything about the structure of `tree` and the values within
it, then I see no reason to use any other data structure in an exhaustive
search.

Still, it's interesting to consider what happens when we use some other
data structure.

With a Priority Queue
---------------------
What about a heap?  The next element visited is always the _smallest_ (or the
_largest_) among those <em>to_visit</em>, according to some comparison
function.
```c++
#include <queue>
#include <vector>

template <typename Value>
struct Greater {
    bool operator(const Tree<Value>* left, const Tree<Value>* right) const {
        return left->value > right->value;
    }
};

template <typename Value>
struct PriorityQueue : public std::priority_queue<const Tree<Value>*, std::vector<const Tree<Value>*>, Greater<Value>> {
    // Return the smallest element in this queue.
    const Tree<Value>*& next() const {
        return this->top();
    }
};

template <typename Value>
const Tree<Value>* least_first_search(const Tree<Value>& tree, const Value& value) {
    return search(tree, value, PriorityQueue<Value>());
}
```
This is more costly than the vanilla depth-first or breadth-first algorithms,
because operations on the heap (priority queue) are logarithmic in its size
rather than amortized constant.

With a Hash Multiset
--------------------
We could also visit nodes in an expanding pseudorandom order by using a
hash-based container.
```c++
#include <cstddef>
#include <functional>
#include <unordered_set>

template <typename Value>
struct HashValue {
    std::size_t operator()(const Tree<Value>* node) const {
        return std::hash<Value>(node->value)();
    }
};

template <typename Value>
struct HashMultiset : public std::unordered_multiset<const Tree<Value>*, HashValue<Value>> {
    const Tree<Value>* next() const {
        return this->front();
    }

    void pop() {
        erase(this->begin());
    }

    void push(const Tree<Value>* node) {
        insert(node);
    }
};

template <typename Value>
const Tree<Value>* bogo_search(const Tree<Value>& tree, const Value& value) {
    return search(tree, value, HashMultiset<Value>());
}
```
The hash is of a node's value, which is strange.  Stranger still would be
to hash the node's address instead.

Treeeeeessss.......

![tree](tree.svg)
